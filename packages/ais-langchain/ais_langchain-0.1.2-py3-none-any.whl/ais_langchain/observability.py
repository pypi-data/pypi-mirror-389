"""
Observability for AIS-LangChain Integration

Production-grade observability features including:
- Structured logging
- Performance metrics
- Health checks
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

import statistics

T = TypeVar("T")


# ============================================================================
# STRUCTURED LOGGING
# ============================================================================


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class LogEntry:
    """Structured log entry."""

    timestamp: str
    level: LogLevel
    message: str
    context: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class LoggerConfig:
    """Logger configuration."""

    level: LogLevel = LogLevel.INFO
    pretty: bool = False
    handler: Optional[Callable[[LogEntry], None]] = None


class Logger:
    """
    Structured logger with JSON output.

    Singleton pattern for consistent logging across application.
    """

    _instance: Optional["Logger"] = None
    _lock = asyncio.Lock()

    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize logger."""
        self.config = config or LoggerConfig()
        self._setup_handler()

    @classmethod
    async def get_instance(
        cls, config: Optional[LoggerConfig] = None
    ) -> "Logger":
        """
        Get logger singleton instance.

        Args:
            config: Logger configuration (only used on first call)

        Returns:
            Logger instance
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    @classmethod
    def get_instance_sync(
        cls, config: Optional[LoggerConfig] = None
    ) -> "Logger":
        """
        Get logger singleton instance (synchronous).

        Args:
            config: Logger configuration (only used on first call)

        Returns:
            Logger instance
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _setup_handler(self) -> None:
        """Setup default log handler."""
        if self.config.handler is None:
            if self.config.pretty:
                self.config.handler = self._pretty_print_handler
            else:
                self.config.handler = self._json_handler

    def _json_handler(self, entry: LogEntry) -> None:
        """JSON log handler."""
        data = {
            "timestamp": entry.timestamp,
            "level": entry.level.value,
            "message": entry.message,
        }
        if entry.context:
            data["context"] = entry.context
        if entry.error:
            data["error"] = entry.error

        print(json.dumps(data))

    def _pretty_print_handler(self, entry: LogEntry) -> None:
        """Pretty print log handler."""
        # Color codes
        colors = {
            LogLevel.DEBUG: "\033[36m",  # Cyan
            LogLevel.INFO: "\033[32m",  # Green
            LogLevel.WARN: "\033[33m",  # Yellow
            LogLevel.ERROR: "\033[31m",  # Red
        }
        reset = "\033[0m"

        color = colors.get(entry.level, "")
        output = f"{color}[{entry.level.value}]{reset} {entry.message}"

        if entry.context:
            output += f" {json.dumps(entry.context)}"
        if entry.error:
            output += f"\n  Error: {json.dumps(entry.error, indent=2)}"

        print(output)

    def _should_log(self, level: LogLevel) -> bool:
        """Check if level should be logged."""
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]
        return levels.index(level) >= levels.index(self.config.level)

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Internal log method."""
        if not self._should_log(level):
            return

        entry = LogEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            level=level,
            message=message,
            context=context,
            error={
                "type": type(error).__name__,
                "message": str(error),
            }
            if error
            else None,
        )

        if self.config.handler:
            self.config.handler(entry)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, context)

    def warn(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self._log(LogLevel.WARN, message, context)

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, context, error)


# ============================================================================
# METRICS COLLECTION
# ============================================================================


@dataclass
class CounterMetric:
    """Counter metric."""

    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramMetric:
    """Histogram metric."""

    values: List[float] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class GaugeMetric:
    """Gauge metric."""

    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collect performance metrics.

    Supports counters, histograms, and gauges.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.counters: Dict[str, CounterMetric] = {}
        self.histograms: Dict[str, HistogramMetric] = {}
        self.gauges: Dict[str, GaugeMetric] = {}
        self._lock = asyncio.Lock()

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create metric key from name and labels."""
        if not labels:
            return name
        labels_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{labels_str}}}"

    async def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Value to add
            labels: Optional labels
        """
        key = self._make_key(name, labels)

        async with self._lock:
            if key not in self.counters:
                self.counters[key] = CounterMetric(labels=labels or {})
            self.counters[key].value += value

    def increment_counter_sync(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Synchronous version of increment_counter."""
        key = self._make_key(name, labels)

        if key not in self.counters:
            self.counters[key] = CounterMetric(labels=labels or {})
        self.counters[key].value += value

    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a histogram value.

        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels
        """
        key = self._make_key(name, labels)

        async with self._lock:
            if key not in self.histograms:
                self.histograms[key] = HistogramMetric(labels=labels or {})
            self.histograms[key].values.append(value)

    def record_histogram_sync(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Synchronous version of record_histogram."""
        key = self._make_key(name, labels)

        if key not in self.histograms:
            self.histograms[key] = HistogramMetric(labels=labels or {})
        self.histograms[key].values.append(value)

    async def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set a gauge value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels
        """
        key = self._make_key(name, labels)

        async with self._lock:
            if key not in self.gauges:
                self.gauges[key] = GaugeMetric(labels=labels or {})
            self.gauges[key].value = value

    def set_gauge_sync(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Synchronous version of set_gauge."""
        key = self._make_key(name, labels)

        if key not in self.gauges:
            self.gauges[key] = GaugeMetric(labels=labels or {})
        self.gauges[key].value = value

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a histogram.

        Args:
            name: Metric name

        Returns:
            Dict with count, sum, mean, min, max, p50, p95, p99
        """
        if name not in self.histograms:
            return {}

        values = self.histograms[name].values
        if not values:
            return {}

        sorted_values = sorted(values)
        return {
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p50": statistics.median(sorted_values),
            "p95": sorted_values[int(len(sorted_values) * 0.95)]
            if len(sorted_values) > 0
            else 0,
            "p99": sorted_values[int(len(sorted_values) * 0.99)]
            if len(sorted_values) > 0
            else 0,
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.

        Returns:
            Dict with all counters, histograms, and gauges
        """
        return {
            "counters": {
                name: metric.value for name, metric in self.counters.items()
            },
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            },
            "gauges": {name: metric.value for name, metric in self.gauges.items()},
        }

    async def reset(self) -> None:
        """Reset all metrics."""
        async with self._lock:
            self.counters.clear()
            self.histograms.clear()
            self.gauges.clear()


# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================


class PerformanceTracker:
    """
    Track performance of operations.

    Automatically records latency to metrics collector.
    """

    def __init__(
        self, metrics: MetricsCollector, logger: Optional[Logger] = None
    ):
        """
        Initialize performance tracker.

        Args:
            metrics: Metrics collector
            logger: Optional logger
        """
        self.metrics = metrics
        self.logger = logger

    async def track(
        self,
        operation: str,
        fn: Callable[[], Awaitable[T]],
        labels: Optional[Dict[str, str]] = None,
    ) -> T:
        """
        Track performance of an async operation.

        Args:
            operation: Operation name
            fn: Async function to track
            labels: Optional labels

        Returns:
            Result of function call
        """
        start_time = time.time()
        error: Optional[Exception] = None

        try:
            result = await fn()
            return result
        except Exception as e:
            error = e
            raise
        finally:
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000

            metric_labels = {**(labels or {}), "operation": operation}

            if error:
                metric_labels["status"] = "error"
                await self.metrics.increment_counter(
                    f"{operation}_errors_total", 1, metric_labels
                )
            else:
                metric_labels["status"] = "success"
                await self.metrics.increment_counter(
                    f"{operation}_success_total", 1, metric_labels
                )

            await self.metrics.record_histogram(
                f"{operation}_duration_ms", duration_ms, metric_labels
            )

            if self.logger:
                self.logger.debug(
                    f"{operation} completed",
                    {
                        "duration_ms": round(duration_ms, 2),
                        "status": "error" if error else "success",
                        **metric_labels,
                    },
                )


# ============================================================================
# HEALTH CHECKS
# ============================================================================


class HealthStatus(str, Enum):
    """Health status."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class HealthCheckResult:
    """Health check result."""

    status: HealthStatus
    checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))


class HealthChecker:
    """
    Monitor system health.

    Allows registering multiple health checks and aggregating results.
    """

    def __init__(self):
        """Initialize health checker."""
        self.checks: Dict[
            str, Callable[[], Awaitable[Dict[str, Any]]]
        ] = {}
        self._lock = asyncio.Lock()

    def register(
        self,
        name: str,
        check: Callable[[], Awaitable[Dict[str, Any]]],
    ) -> None:
        """
        Register a health check.

        Args:
            name: Check name
            check: Async function returning health status dict
                   Must return: {"status": HealthStatus, "message": str (optional)}
        """
        self.checks[name] = check

    async def check(self) -> HealthCheckResult:
        """
        Run all health checks.

        Returns:
            Aggregated health check result
        """
        results: Dict[str, Dict[str, Any]] = {}
        overall_status = HealthStatus.HEALTHY

        # Run all checks in parallel
        check_tasks = {
            name: asyncio.create_task(check())
            for name, check in self.checks.items()
        }

        for name, task in check_tasks.items():
            try:
                result = await task
                results[name] = result

                # Aggregate status
                check_status = result.get("status", HealthStatus.UNHEALTHY)
                if check_status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif (
                    check_status == HealthStatus.DEGRADED
                    and overall_status != HealthStatus.UNHEALTHY
                ):
                    overall_status = HealthStatus.DEGRADED

            except Exception as error:
                results[name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"Health check failed: {error}",
                }
                overall_status = HealthStatus.UNHEALTHY

        return HealthCheckResult(status=overall_status, checks=results)

    async def is_healthy(self) -> bool:
        """
        Quick health check.

        Returns:
            True if healthy, False otherwise
        """
        result = await self.check()
        return result.status == HealthStatus.HEALTHY
