"""
AIS-LangChain Integration

Production-grade LangChain integration for AIS Protocol.
Connect AIS agents to modern LangGraph workflows with enterprise resilience features.
"""

from .ais_tool import create_ais_tool, create_ais_tools
from .ais_tool_enhanced import ManagedAISTools, create_enhanced_ais_tool
from .observability import (
    HealthChecker,
    HealthStatus,
    Logger,
    LogLevel,
    MetricsCollector,
    PerformanceTracker,
)
from .resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    ConnectionPool,
    ResponseCache,
    RetryConfig,
    with_retry,
)

__version__ = "0.1.3"

__all__ = [
    # Basic tools
    "create_ais_tool",
    "create_ais_tools",
    # Enhanced tools
    "create_enhanced_ais_tool",
    "ManagedAISTools",
    # Observability
    "Logger",
    "LogLevel",
    "MetricsCollector",
    "PerformanceTracker",
    "HealthChecker",
    "HealthStatus",
    # Resilience
    "with_retry",
    "RetryConfig",
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerConfig",
    "ConnectionPool",
    "ResponseCache",
]
