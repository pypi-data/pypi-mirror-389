"""
Resilience Patterns for AIS-LangChain Integration

Production-grade resilience patterns including:
- Retry logic with exponential backoff
- Circuit breaker pattern
- Connection pooling
- Response caching
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


# ============================================================================
# RETRY LOGIC WITH EXPONENTIAL BACKOFF
# ============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    backoff_multiplier: float = 2.0
    max_delay: float = 30.0  # seconds
    jitter: float = 0.1  # 10% jitter
    is_retryable: Callable[[Exception], bool] = field(
        default_factory=lambda: lambda e: True
    )
    on_retry: Optional[Callable[[int, Exception, float], None]] = None


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    config: Optional[RetryConfig] = None,
) -> T:
    """
    Execute an async function with retry logic and exponential backoff.

    Args:
        fn: Async function to execute
        config: Retry configuration

    Returns:
        Result of the function call

    Raises:
        Exception: Last exception if all retries fail
    """
    cfg = config or RetryConfig()
    last_error: Optional[Exception] = None

    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return await fn()
        except Exception as error:
            last_error = error

            # Check if we should retry
            if attempt == cfg.max_attempts:
                break
            if not cfg.is_retryable(error):
                raise

            # Calculate delay with exponential backoff + jitter
            base_delay = cfg.initial_delay * (cfg.backoff_multiplier ** (attempt - 1))
            capped_delay = min(base_delay, cfg.max_delay)
            jitter_amount = capped_delay * cfg.jitter * (2 * (0.5 - (time.time() % 1)))
            delay = max(0, capped_delay + jitter_amount)

            # Call retry callback
            if cfg.on_retry:
                cfg.on_retry(attempt, error, delay)

            # Wait before retry
            await asyncio.sleep(delay)

    # All retries failed
    if last_error:
        raise last_error
    raise RuntimeError("Retry failed with no error")


# ============================================================================
# CIRCUIT BREAKER PATTERN
# ============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Blocking calls due to failures
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Open after N failures
    success_threshold: int = 2  # Close after N successes in HALF_OPEN
    reset_timeout: float = 30.0  # Seconds to wait before HALF_OPEN
    window_duration: float = 60.0  # Seconds to track failures
    on_open: Optional[Callable[[], None]] = None
    on_close: Optional[Callable[[], None]] = None
    on_half_open: Optional[Callable[[], None]] = None


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by opening circuit after threshold failures.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker."""
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failures: List[float] = []
        self.successes: int = 0
        self.next_attempt: float = 0.0
        self._lock = asyncio.Lock()

    async def execute(self, fn: Callable[[], Awaitable[T]]) -> T:
        """
        Execute function through circuit breaker.

        Args:
            fn: Async function to execute

        Returns:
            Result of function call

        Raises:
            RuntimeError: If circuit is OPEN
            Exception: Any exception from the function
        """
        async with self._lock:
            # Check if circuit is OPEN
            if self.state == CircuitState.OPEN:
                if time.time() >= self.next_attempt:
                    # Try transitioning to HALF_OPEN
                    self.state = CircuitState.HALF_OPEN
                    self.successes = 0
                    if self.config.on_half_open:
                        self.config.on_half_open()
                else:
                    raise RuntimeError("Circuit breaker is OPEN - service unavailable")

        try:
            result = await fn()
            await self._on_success()
            return result
        except Exception as error:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.config.success_threshold:
                    # Transition to CLOSED
                    self.state = CircuitState.CLOSED
                    self.failures.clear()
                    self.successes = 0
                    if self.config.on_close:
                        self.config.on_close()
            elif self.state == CircuitState.CLOSED:
                # Clear old failures
                now = time.time()
                self.failures = [
                    t
                    for t in self.failures
                    if now - t < self.config.window_duration
                ]

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            now = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Immediately go back to OPEN
                self.state = CircuitState.OPEN
                self.next_attempt = now + self.config.reset_timeout
                if self.config.on_open:
                    self.config.on_open()
            elif self.state == CircuitState.CLOSED:
                # Add failure and check threshold
                self.failures.append(now)
                # Remove old failures
                self.failures = [
                    t
                    for t in self.failures
                    if now - t < self.config.window_duration
                ]

                if len(self.failures) >= self.config.failure_threshold:
                    # Transition to OPEN
                    self.state = CircuitState.OPEN
                    self.next_attempt = now + self.config.reset_timeout
                    if self.config.on_open:
                        self.config.on_open()

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failures.clear()
        self.successes = 0
        self.next_attempt = 0.0


# ============================================================================
# RESPONSE CACHE
# ============================================================================


class ResponseCache:
    """
    TTL-based response cache with automatic cleanup.

    Caches responses to reduce latency and agent load.
    """

    def __init__(self, ttl: float = 60.0):
        """
        Initialize response cache.

        Args:
            ttl: Time-to-live in seconds
        """
        self.ttl = ttl
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    def _make_key(self, capability: str, params: Any) -> str:
        """
        Create cache key from capability and parameters.

        Args:
            capability: Capability name
            params: Call parameters

        Returns:
            Cache key
        """
        params_str = json.dumps(params, sort_keys=True)
        key = f"{capability}:{params_str}"
        return hashlib.sha256(key.encode()).hexdigest()

    async def get(self, capability: str, params: Any) -> Optional[Any]:
        """
        Get cached response if available and not expired.

        Args:
            capability: Capability name
            params: Call parameters

        Returns:
            Cached response or None
        """
        key = self._make_key(capability, params)

        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if time.time() < expires_at:
                    return value
                else:
                    # Expired, remove it
                    del self._cache[key]

        return None

    async def set(self, capability: str, params: Any, value: Any) -> None:
        """
        Cache a response.

        Args:
            capability: Capability name
            params: Call parameters
            value: Response to cache
        """
        key = self._make_key(capability, params)
        expires_at = time.time() + self.ttl

        async with self._lock:
            self._cache[key] = (value, expires_at)

    async def clear(self) -> None:
        """Clear all cached responses."""
        async with self._lock:
            self._cache.clear()

    async def cleanup(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        async with self._lock:
            expired_keys = [
                key
                for key, (_, expires_at) in self._cache.items()
                if now >= expires_at
            ]
            for key in expired_keys:
                del self._cache[key]

    def start_cleanup_loop(self, interval: float = 60.0) -> None:
        """
        Start automatic cleanup loop.

        Args:
            interval: Cleanup interval in seconds
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(
                self._cleanup_loop(interval)
            )

    async def _cleanup_loop(self, interval: float) -> None:
        """Periodic cleanup task."""
        while True:
            await asyncio.sleep(interval)
            await self.cleanup()

    def stop_cleanup_loop(self) -> None:
        """Stop automatic cleanup loop."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        now = time.time()
        total = len(self._cache)
        expired = sum(
            1
            for _, expires_at in self._cache.values()
            if now >= expires_at
        )
        valid = total - expired

        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "ttl_seconds": self.ttl,
        }


# ============================================================================
# CONNECTION POOL
# ============================================================================


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pool."""

    min_size: int = 1
    max_size: int = 10
    acquire_timeout: float = 30.0  # seconds
    idle_timeout: float = 300.0  # 5 minutes


class ConnectionPool:
    """
    Generic connection pool for efficient resource management.

    Note: This is a simplified implementation. For production use with AIS,
    consider using aiohttp's built-in connection pooling.
    """

    def __init__(
        self,
        factory: Callable[[], Awaitable[Any]],
        config: Optional[ConnectionPoolConfig] = None,
    ):
        """
        Initialize connection pool.

        Args:
            factory: Async function to create new connections
            config: Pool configuration
        """
        self.factory = factory
        self.config = config or ConnectionPoolConfig()
        self._available: List[Any] = []
        self._in_use: int = 0
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)

    async def acquire(self) -> Any:
        """
        Acquire a connection from the pool.

        Returns:
            Connection object

        Raises:
            TimeoutError: If acquisition timeout exceeded
        """
        async with self._condition:
            # Wait for available connection
            start_time = time.time()
            while True:
                # Try to get from pool
                if self._available:
                    conn = self._available.pop()
                    self._in_use += 1
                    return conn

                # Try to create new connection
                if self._in_use < self.config.max_size:
                    conn = await self.factory()
                    self._in_use += 1
                    return conn

                # Wait for connection to be released
                elapsed = time.time() - start_time
                if elapsed >= self.config.acquire_timeout:
                    raise TimeoutError("Connection pool acquisition timeout")

                timeout = self.config.acquire_timeout - elapsed
                await asyncio.wait_for(
                    self._condition.wait(),
                    timeout=timeout
                )

    async def release(self, conn: Any) -> None:
        """
        Release a connection back to the pool.

        Args:
            conn: Connection to release
        """
        async with self._condition:
            self._in_use -= 1
            if len(self._available) < self.config.max_size:
                self._available.append(conn)
            self._condition.notify()

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            # Close available connections
            for conn in self._available:
                if hasattr(conn, "close"):
                    await conn.close()
            self._available.clear()
            self._in_use = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Dict with pool stats
        """
        return {
            "available": len(self._available),
            "in_use": self._in_use,
            "total": len(self._available) + self._in_use,
            "min_size": self.config.min_size,
            "max_size": self.config.max_size,
        }
