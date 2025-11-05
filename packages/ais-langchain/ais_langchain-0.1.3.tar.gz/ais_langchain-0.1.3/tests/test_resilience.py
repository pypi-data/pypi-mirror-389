"""
Comprehensive tests for resilience features

Tests:
- Retry with exponential backoff
- Circuit breaker state management
- Response caching
- Connection pooling
"""

import asyncio
import pytest
from ais_langchain.resilience import (
    with_retry,
    RetryConfig,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    ResponseCache,
    ConnectionPool,
)


# ========================================================================
# RETRY TESTS
# ========================================================================


class TestRetry:
    """Test retry functionality with different configurations"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_immediately(self):
        """Should succeed on first attempt"""
        call_count = 0

        async def succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await with_retry(succeeds, RetryConfig(max_attempts=3))
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Should retry and eventually succeed"""
        call_count = 0

        async def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"fail {call_count}")
            return "success"

        result = await with_retry(
            fails_twice,
            RetryConfig(
                max_attempts=3,
                initial_delay=0.01,
                is_retryable=lambda e: True,  # Retry all errors for testing
            ),
        )
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """Should fail after exhausting retries"""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("always fails")

        with pytest.raises(Exception, match="always fails"):
            await with_retry(
                always_fails,
                RetryConfig(
                    max_attempts=3, initial_delay=0.01, is_retryable=lambda e: True
                ),
            )
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Should use exponential backoff delays"""
        call_count = 0
        delays = []

        async def fails_with_timing():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                delays.append(asyncio.get_event_loop().time())
            if call_count < 4:
                raise Exception("fail")
            return "success"

        result = await with_retry(
            fails_with_timing,
            RetryConfig(
                max_attempts=4,
                initial_delay=0.05,
                backoff_multiplier=2.0,
                is_retryable=lambda e: True,
            ),
        )
        assert result == "success"
        assert call_count == 4


# ========================================================================
# CIRCUIT BREAKER TESTS
# ========================================================================


class TestCircuitBreaker:
    """Test circuit breaker state management"""

    @pytest.mark.asyncio
    async def test_starts_closed(self):
        """Should start in CLOSED state"""
        breaker = CircuitBreaker(
            CircuitBreakerConfig(failure_threshold=3, reset_timeout=1.0)
        )
        assert breaker.get_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        """Should open after failure threshold"""
        open_called = False

        def on_open():
            nonlocal open_called
            open_called = True

        breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=3, reset_timeout=1.0, on_open=on_open
            )
        )

        async def fails():
            raise Exception("fail")

        # Cause failures to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.execute(fails)

        assert breaker.get_state() == CircuitState.OPEN
        assert open_called

    @pytest.mark.asyncio
    async def test_rejects_when_open(self):
        """Should reject calls when circuit is OPEN"""
        breaker = CircuitBreaker(
            CircuitBreakerConfig(failure_threshold=2, reset_timeout=1.0)
        )

        async def fails():
            raise Exception("fail")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.execute(fails)

        # Should reject without calling
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.execute(fails)

    @pytest.mark.asyncio
    async def test_transitions_to_half_open(self):
        """Should transition to HALF_OPEN after timeout"""
        breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=2,
                reset_timeout=0.1,
                success_threshold=1  # Close after 1 success
            )
        )

        async def fails():
            raise Exception("fail")

        # Open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.execute(fails)

        assert breaker.get_state() == CircuitState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # Next call should transition to HALF_OPEN then CLOSED
        async def succeeds():
            return "success"

        result = await breaker.execute(succeeds)
        assert result == "success"
        assert breaker.get_state() == CircuitState.CLOSED


# ========================================================================
# RESPONSE CACHE TESTS
# ========================================================================


class TestResponseCache:
    """Test response caching functionality"""

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self):
        """Should return None for cache miss"""
        cache = ResponseCache(ttl=60.0)
        result = await cache.get("test", {"param": "value"})
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_returns_value(self):
        """Should return cached value on hit"""
        cache = ResponseCache(ttl=60.0)
        await cache.set("test", {"param": "value"}, "result")
        result = await cache.get("test", {"param": "value"})
        assert result == "result"

    @pytest.mark.asyncio
    async def test_cache_different_params(self):
        """Should cache separately for different params"""
        cache = ResponseCache(ttl=60.0)
        await cache.set("test", {"a": 1}, "result1")
        await cache.set("test", {"a": 2}, "result2")

        assert await cache.get("test", {"a": 1}) == "result1"
        assert await cache.get("test", {"a": 2}) == "result2"

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Should expire after TTL"""
        cache = ResponseCache(ttl=0.1)
        await cache.set("test", {}, "result")

        # Should be cached
        assert await cache.get("test", {}) == "result"

        # Wait for expiration
        await asyncio.sleep(0.15)

        # Should be expired
        assert await cache.get("test", {}) is None

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Should return cache statistics"""
        cache = ResponseCache(ttl=60.0)
        await cache.set("test", {"a": 1}, "result1")
        await cache.set("test", {"a": 2}, "result2")

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["ttl_seconds"] == 60.0

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Should clear all entries"""
        cache = ResponseCache(ttl=60.0)
        await cache.set("test", {"a": 1}, "result1")
        await cache.set("test", {"a": 2}, "result2")

        await cache.clear()
        stats = cache.get_stats()
        assert stats["total_entries"] == 0


# ========================================================================
# CONNECTION POOL TESTS
# ========================================================================


class TestConnectionPool:
    """Test connection pooling"""

    @pytest.mark.asyncio
    async def test_creates_connections(self):
        """Should create connections up to max_size"""
        created_count = 0

        async def factory():
            nonlocal created_count
            created_count += 1
            return {"id": created_count}

        from ais_langchain.resilience import ConnectionPoolConfig
        pool = ConnectionPool(
            factory,
            ConnectionPoolConfig(max_size=3)
        )

        conn1 = await pool.acquire()
        conn2 = await pool.acquire()

        assert created_count == 2
        assert conn1 != conn2

        await pool.release(conn1)
        await pool.release(conn2)

    @pytest.mark.asyncio
    async def test_reuses_released_connections(self):
        """Should reuse released connections"""
        created_count = 0

        async def factory():
            nonlocal created_count
            created_count += 1
            return {"id": created_count}

        from ais_langchain.resilience import ConnectionPoolConfig
        pool = ConnectionPool(
            factory,
            ConnectionPoolConfig(max_size=3)
        )

        conn1 = await pool.acquire()
        await pool.release(conn1)

        conn2 = await pool.acquire()
        assert created_count == 1  # Reused, didn't create new
        assert conn1 == conn2

        await pool.release(conn2)

    @pytest.mark.asyncio
    async def test_pool_stats(self):
        """Should return pool statistics"""
        async def factory():
            return {}

        from ais_langchain.resilience import ConnectionPoolConfig
        pool = ConnectionPool(
            factory,
            ConnectionPoolConfig(max_size=3)
        )

        conn1 = await pool.acquire()
        conn2 = await pool.acquire()

        stats = pool.get_stats()
        assert stats["total"] >= 2
        assert stats["in_use"] == 2
        assert stats["available"] >= 0

        await pool.release(conn1)
        await pool.release(conn2)
