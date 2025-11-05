"""
Comprehensive tests for observability features

Tests:
- Structured logging
- Metrics collection
- Performance tracking
- Health checks
"""

import asyncio
import pytest
from ais_langchain.observability import (
    Logger,
    LoggerConfig,
    LogLevel,
    LogEntry,
    MetricsCollector,
    PerformanceTracker,
    HealthChecker,
    HealthStatus,
)


# ========================================================================
# LOGGER TESTS
# ========================================================================


class TestLogger:
    """Test structured logging"""

    def setup_method(self):
        """Reset logger singleton before each test"""
        Logger._instance = None

    @pytest.mark.asyncio
    async def test_logger_singleton(self):
        """Should return same instance"""
        logger1 = await Logger.get_instance()
        logger2 = await Logger.get_instance()
        assert logger1 is logger2

    def test_logger_sync_singleton(self):
        """Should return same instance (sync)"""
        logger1 = Logger.get_instance_sync()
        logger2 = Logger.get_instance_sync()
        assert logger1 is logger2

    def test_log_levels(self):
        """Should log at different levels"""
        logged_entries = []

        def capture_handler(entry: LogEntry):
            logged_entries.append(entry)

        config = LoggerConfig(level=LogLevel.DEBUG, handler=capture_handler)
        logger = Logger(config)

        logger.debug("debug msg", {"key": "value"})
        logger.info("info msg")
        logger.warn("warn msg")
        logger.error("error msg")

        assert len(logged_entries) == 4
        assert logged_entries[0].level == LogLevel.DEBUG
        assert logged_entries[1].level == LogLevel.INFO
        assert logged_entries[2].level == LogLevel.WARN
        assert logged_entries[3].level == LogLevel.ERROR

    def test_log_filtering(self):
        """Should filter logs based on level"""
        logged_entries = []

        def capture_handler(entry: LogEntry):
            logged_entries.append(entry)

        config = LoggerConfig(level=LogLevel.WARN, handler=capture_handler)
        logger = Logger(config)

        logger.debug("debug")
        logger.info("info")
        logger.warn("warn")
        logger.error("error")

        assert len(logged_entries) == 2  # Only WARN and ERROR
        assert all(
            e.level in [LogLevel.WARN, LogLevel.ERROR] for e in logged_entries
        )

    def test_log_with_context(self):
        """Should include context in log"""
        logged_entries = []

        def capture_handler(entry: LogEntry):
            logged_entries.append(entry)

        config = LoggerConfig(handler=capture_handler)
        logger = Logger(config)

        logger.info("test", {"user": "alice", "action": "login"})

        assert len(logged_entries) == 1
        assert logged_entries[0].context == {"user": "alice", "action": "login"}

    def test_log_with_error(self):
        """Should include error in log"""
        logged_entries = []

        def capture_handler(entry: LogEntry):
            logged_entries.append(entry)

        config = LoggerConfig(handler=capture_handler)
        logger = Logger(config)

        error = Exception("test error")
        logger.error("error occurred", error=error)

        assert len(logged_entries) == 1
        assert logged_entries[0].error is not None
        assert logged_entries[0].error["type"] == "Exception"
        assert logged_entries[0].error["message"] == "test error"


# ========================================================================
# METRICS TESTS
# ========================================================================


class TestMetrics:
    """Test metrics collection"""

    @pytest.mark.asyncio
    async def test_counter_increment(self):
        """Should increment counter"""
        metrics = MetricsCollector()

        await metrics.increment_counter("requests", 1)
        await metrics.increment_counter("requests", 2)

        all_metrics = metrics.get_all_metrics()
        assert all_metrics["counters"]["requests"] == 3

    def test_counter_increment_sync(self):
        """Should increment counter (sync)"""
        metrics = MetricsCollector()

        metrics.increment_counter_sync("requests", 1)
        metrics.increment_counter_sync("requests", 2)

        all_metrics = metrics.get_all_metrics()
        assert all_metrics["counters"]["requests"] == 3

    @pytest.mark.asyncio
    async def test_counter_with_labels(self):
        """Should track counters with different labels separately"""
        metrics = MetricsCollector()

        await metrics.increment_counter("requests", 1, {"endpoint": "/api"})
        await metrics.increment_counter("requests", 2, {"endpoint": "/api"})
        await metrics.increment_counter("requests", 1, {"endpoint": "/web"})

        all_metrics = metrics.get_all_metrics()
        # Labels format: {k=v} without quotes
        assert all_metrics["counters"]["requests{endpoint=/api}"] == 3
        assert all_metrics["counters"]["requests{endpoint=/web}"] == 1

    @pytest.mark.asyncio
    async def test_histogram_recording(self):
        """Should record histogram values"""
        metrics = MetricsCollector()

        await metrics.record_histogram("latency", 100)
        await metrics.record_histogram("latency", 200)
        await metrics.record_histogram("latency", 150)

        stats = metrics.get_histogram_stats("latency")
        assert stats["count"] == 3
        assert stats["sum"] == 450
        assert stats["mean"] == 150
        assert stats["min"] == 100
        assert stats["max"] == 200

    def test_histogram_recording_sync(self):
        """Should record histogram values (sync)"""
        metrics = MetricsCollector()

        metrics.record_histogram_sync("latency", 100)
        metrics.record_histogram_sync("latency", 200)
        metrics.record_histogram_sync("latency", 150)

        stats = metrics.get_histogram_stats("latency")
        assert stats["count"] == 3
        assert stats["sum"] == 450
        assert stats["mean"] == 150

    @pytest.mark.asyncio
    async def test_histogram_percentiles(self):
        """Should calculate percentiles correctly"""
        metrics = MetricsCollector()

        # Add 100 values: 1, 2, 3, ..., 100
        for i in range(1, 101):
            await metrics.record_histogram("values", i)

        stats = metrics.get_histogram_stats("values")
        assert stats["count"] == 100
        assert stats["p50"] == 50.5  # Median
        assert stats["p95"] == 96  # int(100 * 0.95) = index 95 = value 96 (sorted 1..100)
        assert stats["p99"] == 100  # int(100 * 0.99) = index 99 = value 100

    @pytest.mark.asyncio
    async def test_gauge_setting(self):
        """Should set gauge values"""
        metrics = MetricsCollector()

        await metrics.set_gauge("memory", 1024)
        await metrics.set_gauge("memory", 2048)  # Overwrite

        all_metrics = metrics.get_all_metrics()
        assert all_metrics["gauges"]["memory"] == 2048

    def test_gauge_setting_sync(self):
        """Should set gauge values (sync)"""
        metrics = MetricsCollector()

        metrics.set_gauge_sync("memory", 1024)
        metrics.set_gauge_sync("memory", 2048)

        all_metrics = metrics.get_all_metrics()
        assert all_metrics["gauges"]["memory"] == 2048

    @pytest.mark.asyncio
    async def test_histogram_stats_empty(self):
        """Should return empty dict for non-existent histogram"""
        metrics = MetricsCollector()
        stats = metrics.get_histogram_stats("nonexistent")
        assert stats == {}

    @pytest.mark.asyncio
    async def test_reset_metrics(self):
        """Should reset all metrics"""
        metrics = MetricsCollector()

        await metrics.increment_counter("requests", 5)
        await metrics.record_histogram("latency", 100)
        await metrics.set_gauge("memory", 1024)

        await metrics.reset()

        all_metrics = metrics.get_all_metrics()
        assert len(all_metrics["counters"]) == 0
        assert len(all_metrics["histograms"]) == 0
        assert len(all_metrics["gauges"]) == 0


# ========================================================================
# PERFORMANCE TRACKER TESTS
# ========================================================================


class TestPerformanceTracker:
    """Test performance tracking"""

    @pytest.mark.asyncio
    async def test_track_successful_operation(self):
        """Should track successful operation"""
        metrics = MetricsCollector()
        tracker = PerformanceTracker(metrics)

        async def operation():
            await asyncio.sleep(0.01)
            return "success"

        result = await tracker.track("test_op", operation)

        assert result == "success"

        all_metrics = metrics.get_all_metrics()
        # Check success counter (with operation and status labels)
        success_key = "test_op_success_total{operation=test_op,status=success}"
        assert success_key in all_metrics["counters"]
        assert all_metrics["counters"][success_key] == 1

    @pytest.mark.asyncio
    async def test_track_failed_operation(self):
        """Should track failed operation"""
        metrics = MetricsCollector()
        tracker = PerformanceTracker(metrics)

        async def operation():
            raise Exception("test error")

        with pytest.raises(Exception, match="test error"):
            await tracker.track("test_op", operation)

        all_metrics = metrics.get_all_metrics()
        # Check error counter
        error_key = "test_op_errors_total{operation=test_op,status=error}"
        assert error_key in all_metrics["counters"]
        assert all_metrics["counters"][error_key] == 1

    @pytest.mark.asyncio
    async def test_track_duration(self):
        """Should record operation duration"""
        metrics = MetricsCollector()
        tracker = PerformanceTracker(metrics)

        async def operation():
            await asyncio.sleep(0.05)  # 50ms
            return "done"

        await tracker.track("test_op", operation)

        # Check duration histogram
        duration_key = "test_op_duration_ms{operation=test_op,status=success}"
        all_metrics = metrics.get_all_metrics()
        assert duration_key in all_metrics["histograms"]
        stats = all_metrics["histograms"][duration_key]
        assert stats["count"] == 1
        assert stats["mean"] >= 45  # At least 45ms (accounting for overhead)

    @pytest.mark.asyncio
    async def test_track_with_labels(self):
        """Should include custom labels in metrics"""
        metrics = MetricsCollector()
        tracker = PerformanceTracker(metrics)

        async def operation():
            return "done"

        await tracker.track("test_op", operation, {"user": "alice"})

        all_metrics = metrics.get_all_metrics()
        # Should have labels in key
        assert any("user=alice" in key for key in all_metrics["counters"].keys())


# ========================================================================
# HEALTH CHECKER TESTS
# ========================================================================


class TestHealthChecker:
    """Test health checking"""

    @pytest.mark.asyncio
    async def test_no_checks_is_healthy(self):
        """Should be healthy with no checks"""
        checker = HealthChecker()
        result = await checker.check()
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_healthy_check(self):
        """Should report healthy status"""
        checker = HealthChecker()

        async def db_check():
            return {"status": HealthStatus.HEALTHY, "message": "DB connected"}

        checker.register("database", db_check)
        result = await checker.check()

        assert result.status == HealthStatus.HEALTHY
        assert "database" in result.checks
        assert result.checks["database"]["status"] == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_degraded_check(self):
        """Should report degraded status"""
        checker = HealthChecker()

        async def db_check():
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Slow responses",
            }

        checker.register("database", db_check)
        result = await checker.check()

        assert result.status == HealthStatus.DEGRADED
        assert result.checks["database"]["status"] == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_unhealthy_check(self):
        """Should report unhealthy status"""
        checker = HealthChecker()

        async def db_check():
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": "Cannot connect",
            }

        checker.register("database", db_check)
        result = await checker.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert result.checks["database"]["status"] == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_mixed_checks(self):
        """Should aggregate multiple checks"""
        checker = HealthChecker()

        async def db_check():
            return {"status": HealthStatus.HEALTHY}

        async def cache_check():
            return {"status": HealthStatus.DEGRADED}

        checker.register("database", db_check)
        checker.register("cache", cache_check)

        result = await checker.check()

        # Overall should be DEGRADED (worst of HEALTHY and DEGRADED)
        assert result.status == HealthStatus.DEGRADED
        assert len(result.checks) == 2

    @pytest.mark.asyncio
    async def test_check_failure(self):
        """Should handle check failures gracefully"""
        checker = HealthChecker()

        async def failing_check():
            raise Exception("Check failed")

        checker.register("broken", failing_check)
        result = await checker.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert result.checks["broken"]["status"] == HealthStatus.UNHEALTHY
        assert "Health check failed" in result.checks["broken"]["message"]

    @pytest.mark.asyncio
    async def test_is_healthy(self):
        """Should return boolean health status"""
        checker = HealthChecker()

        async def healthy_check():
            return {"status": HealthStatus.HEALTHY}

        checker.register("test", healthy_check)
        assert await checker.is_healthy() == True

        # Add unhealthy check
        async def unhealthy_check():
            return {"status": HealthStatus.UNHEALTHY}

        checker.register("broken", unhealthy_check)
        assert await checker.is_healthy() == False
