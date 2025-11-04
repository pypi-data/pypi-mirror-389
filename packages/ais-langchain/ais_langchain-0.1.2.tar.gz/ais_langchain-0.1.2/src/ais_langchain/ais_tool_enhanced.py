"""
Enhanced AIS Tool Adapters for Production Use

Production-grade tools with enterprise resilience features:
- Retry logic with exponential backoff
- Circuit breaker pattern
- Response caching
- Structured logging
- Performance metrics
- Health checks
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from .ais_tool import create_ais_tool, _format_result
from .observability import (
    HealthChecker,
    HealthStatus,
    Logger,
    LoggerConfig,
    LogLevel,
    MetricsCollector,
    PerformanceTracker,
)
from .resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    ResponseCache,
    RetryConfig,
    with_retry,
)


@dataclass
class EnhancedAISToolConfig:
    """Configuration for enhanced AIS tool."""

    client: Any  # AISClient
    capability: str
    name: Optional[str] = None
    description: Optional[str] = None
    args_schema: Optional[Type[BaseModel]] = None
    timeout: Optional[float] = None
    retry: Optional[RetryConfig] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    cache: bool = False
    cache_ttl: float = 60.0
    logger: Optional[Logger] = None
    metrics: Optional[MetricsCollector] = None


def create_enhanced_ais_tool(config: EnhancedAISToolConfig) -> StructuredTool:
    """
    Create a production-grade LangChain tool with resilience features.

    Args:
        config: Tool configuration

    Returns:
        LangChain StructuredTool with resilience features

    Example:
        ```python
        from ais_protocol import AISClient
        from ais_langchain import (
            create_enhanced_ais_tool,
            EnhancedAISToolConfig,
            RetryConfig,
            CircuitBreakerConfig,
            Logger,
            LogLevel,
            MetricsCollector,
        )

        logger = Logger.get_instance_sync(LoggerConfig(level=LogLevel.INFO))
        metrics = MetricsCollector()

        client = AISClient(agent_id="agent://example.com/client")
        await client.connect("http://localhost:8000")

        calculator = create_enhanced_ais_tool(EnhancedAISToolConfig(
            client=client,
            capability="calculate",
            retry=RetryConfig(max_attempts=3, initial_delay=1.0),
            circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
            cache=True,
            cache_ttl=60.0,
            logger=logger,
            metrics=metrics
        ))
        ```
    """
    tool_name = config.name or config.capability
    tool_description = (
        config.description or f"Call AIS capability: {config.capability}"
    )

    # Initialize resilience components
    circuit_breaker = None
    if config.circuit_breaker:

        def on_open() -> None:
            if config.logger:
                config.logger.warn(
                    f"Circuit breaker OPEN for {config.capability}"
                )

        def on_close() -> None:
            if config.logger:
                config.logger.info(
                    f"Circuit breaker CLOSED for {config.capability}"
                )

        circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                **{
                    **config.circuit_breaker.__dict__,
                    "on_open": on_open,
                    "on_close": on_close,
                }
            )
        )

    response_cache = ResponseCache(config.cache_ttl) if config.cache else None

    # Create performance tracker
    performance_tracker = None
    if config.metrics:
        performance_tracker = PerformanceTracker(config.metrics, config.logger)

    # Create retry config with logging
    retry_config = None
    if config.retry:

        def on_retry(attempt: int, error: Exception, delay: float) -> None:
            if config.logger:
                config.logger.warn(
                    f"Retrying {config.capability}",
                    {
                        "attempt": attempt,
                        "error": str(error),
                        "delay_ms": round(delay * 1000, 2),
                    },
                )

        retry_config = RetryConfig(
            **{**config.retry.__dict__, "on_retry": on_retry}
        )

    async def _call_capability(**kwargs: Any) -> str:
        """Internal function with resilience features."""
        # Log call
        if config.logger:
            config.logger.debug(
                f"Calling AIS capability: {config.capability}", {"params": kwargs}
            )

        # Check cache first
        if response_cache:
            cached = await response_cache.get(config.capability, kwargs)
            if cached is not None:
                if config.metrics:
                    config.metrics.increment_counter_sync(
                        "ais_cache_hit_total",
                        1,
                        {"capability": config.capability},
                    )
                if config.logger:
                    config.logger.debug(
                        f"Cache hit for {config.capability}", {"params": kwargs}
                    )
                return cached

        # Increment cache miss
        if response_cache and config.metrics:
            config.metrics.increment_counter_sync(
                "ais_cache_miss_total", 1, {"capability": config.capability}
            )

        # Define call function
        async def call_fn() -> str:
            options = {"timeout": config.timeout} if config.timeout else None
            result = await config.client.call(
                config.capability, kwargs, options
            )
            return _format_result(result)

        # Apply circuit breaker
        async def protected_call() -> str:
            if circuit_breaker:
                return await circuit_breaker.execute(call_fn)
            return await call_fn()

        # Apply retry
        async def retried_call() -> str:
            if retry_config:
                return await with_retry(protected_call, retry_config)
            return await protected_call()

        # Track performance
        async def tracked_call() -> str:
            if performance_tracker:
                return await performance_tracker.track(
                    "ais_capability_call",
                    retried_call,
                    {"capability": config.capability},
                )
            return await retried_call()

        try:
            result = await tracked_call()

            # Cache result
            if response_cache:
                await response_cache.set(config.capability, kwargs, result)

            return result

        except Exception as error:
            if config.logger:
                config.logger.error(
                    f"Error calling AIS capability '{config.capability}'",
                    error,
                    {"params": kwargs},
                )
            return f"Error calling AIS capability '{config.capability}': {str(error)}"

    # Create structured tool
    if config.args_schema:
        tool = StructuredTool(
            name=tool_name,
            description=tool_description,
            args_schema=config.args_schema,
            coroutine=_call_capability,
        )
    else:
        # Create basic tool
        tool = create_ais_tool(
            client=config.client,
            capability=config.capability,
            name=tool_name,
            description=tool_description,
            timeout=config.timeout,
        )

    return tool


class ManagedAISTools:
    """
    Manage multiple AIS tools with shared infrastructure.

    Provides centralized management of:
    - Shared logger
    - Shared metrics collector
    - Shared response cache
    - Circuit breakers for all tools
    - Health monitoring
    """

    def __init__(
        self,
        client: Any,  # AISClient
        logger: Optional[Logger] = None,
        metrics: Optional[MetricsCollector] = None,
        cache: Optional[ResponseCache] = None,
        cache_ttl: float = 60.0,
    ):
        """
        Initialize managed tools.

        Args:
            client: AIS client instance
            logger: Optional shared logger
            metrics: Optional shared metrics collector
            cache: Optional shared response cache
            cache_ttl: Cache TTL in seconds
        """
        self.client = client
        self.logger = logger or Logger.get_instance_sync()
        self.metrics = metrics or MetricsCollector()
        self.cache = cache or ResponseCache(cache_ttl)
        self.health_checker = HealthChecker()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.tools: List[StructuredTool] = []

        # Register default health check
        self._register_default_health_checks()

    def _register_default_health_checks(self) -> None:
        """Register default health checks."""

        async def check_client() -> Dict[str, Any]:
            """Check if client is connected."""
            is_connected = getattr(self.client, "is_connected", lambda: True)()
            return {
                "status": HealthStatus.HEALTHY
                if is_connected
                else HealthStatus.UNHEALTHY,
                "message": "AIS client connected"
                if is_connected
                else "AIS client disconnected",
            }

        self.health_checker.register("ais_client", check_client)

    def create_tool(
        self,
        capability: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        args_schema: Optional[Type[BaseModel]] = None,
        retry: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        cache: bool = True,
        timeout: Optional[float] = None,
    ) -> StructuredTool:
        """
        Create a single enhanced tool.

        Args:
            capability: Capability name
            name: Tool name
            description: Tool description
            args_schema: Pydantic args schema
            retry: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
            cache: Enable caching
            timeout: Call timeout

        Returns:
            Enhanced LangChain tool
        """
        tool = create_enhanced_ais_tool(
            EnhancedAISToolConfig(
                client=self.client,
                capability=capability,
                name=name,
                description=description,
                args_schema=args_schema,
                timeout=timeout,
                retry=retry,
                circuit_breaker=circuit_breaker_config,
                cache=cache,
                cache_ttl=self.cache.ttl,
                logger=self.logger,
                metrics=self.metrics,
            )
        )

        self.tools.append(tool)
        return tool

    def create_all_tools(
        self,
        retry: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreakerConfig] = None,
        cache: bool = True,
        schemas: Optional[Dict[str, Type[BaseModel]]] = None,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> List[StructuredTool]:
        """
        Create tools from all capabilities.

        Args:
            retry: Default retry configuration
            circuit_breaker: Default circuit breaker configuration
            cache: Enable caching by default
            schemas: Dict mapping capability names to Pydantic schemas
            include: Only include these capabilities
            exclude: Exclude these capabilities

        Returns:
            List of enhanced tools
        """
        capabilities = self.client.server_capabilities()
        tools: List[StructuredTool] = []

        for cap in capabilities:
            # Get capability name
            if isinstance(cap, str):
                cap_name = cap
                cap_desc = None
            elif isinstance(cap, dict):
                cap_name = cap.get("name", "")
                cap_desc = cap.get("description")
            else:
                cap_name = getattr(cap, "name", str(cap))
                cap_desc = getattr(cap, "description", None)

            # Apply filters
            if include and cap_name not in include:
                continue
            if exclude and cap_name in exclude:
                continue

            # Get schema if provided
            args_schema = schemas.get(cap_name) if schemas else None

            # Create tool
            tool = self.create_tool(
                capability=cap_name,
                description=cap_desc,
                args_schema=args_schema,
                retry=retry,
                circuit_breaker_config=circuit_breaker,
                cache=cache,
            )
            tools.append(tool)

        return tools

    async def get_health(self) -> Dict[str, Any]:
        """
        Get health status.

        Returns:
            Health check result
        """
        result = await self.health_checker.check()
        return {
            "status": result.status.value,
            "checks": result.checks,
            "timestamp": result.timestamp,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.

        Returns:
            All metrics
        """
        return self.metrics.get_all_metrics()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache stats
        """
        return self.cache.get_stats()

    async def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get complete diagnostics.

        Returns:
            Health, metrics, and cache stats
        """
        return {
            "health": await self.get_health(),
            "metrics": self.get_metrics(),
            "cache": self.get_cache_stats(),
            "circuit_breakers": {
                name: cb.get_state().value
                for name, cb in self.circuit_breakers.items()
            },
        }

    async def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()

    async def clear_cache(self) -> None:
        """Clear response cache."""
        await self.cache.clear()
