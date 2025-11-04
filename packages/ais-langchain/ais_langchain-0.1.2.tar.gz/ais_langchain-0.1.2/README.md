# ais-langchain

**Production-grade LangChain integration for AIS Protocol**

Connect AIS agents to modern LangGraph workflows with enterprise resilience features.

[![PyPI version](https://img.shields.io/pypi/v/ais-langchain.svg)](https://pypi.org/project/ais-langchain/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 What is This?

This package enables **seamless integration** between [AIS Protocol](https://github.com/ais-protocol/ais-python) agents and [LangChain](https://python.langchain.com/)'s modern LangGraph framework.

**Think:** HTTP for AI agents + LangChain's powerful workflows = **Multi-Agent Nirvana** 🚀

---

## ✨ Features

### 🏗️ Production-Ready

- ✅ **Modern LangGraph** - Uses latest `langgraph` with `create_react_agent`
- ✅ **Automatic Retry** - Exponential backoff with configurable jitter
- ✅ **Circuit Breaker** - Prevents cascading failures
- ✅ **Response Caching** - Reduce latency up to 160x
- ✅ **Connection Pooling** - Efficient resource usage
- ✅ **Structured Logging** - Production-grade observability
- ✅ **Performance Metrics** - Track latency, success/failure rates
- ✅ **Health Checks** - Monitor agent availability
- ✅ **Type Safety** - Full Python type hints

### 🎭 Multi-Agent Orchestration

- ✅ **ManagedAISTools** - Coordinate multiple specialized agents
- ✅ **Dynamic Routing** - Route to agents based on capabilities
- ✅ **Capability Discovery** - Automatic tool generation
- ✅ **Session Management** - Stateful multi-turn conversations

---

## 🚀 Quick Start

### Installation

```bash
pip install ais-langchain ais-protocol langchain-core langgraph langchain-openai
```

### Basic Usage

```python
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ais_protocol import AISClient
from ais_langchain import create_enhanced_ais_tool, EnhancedAISToolConfig, RetryConfig, CircuitBreakerConfig
from pydantic import BaseModel, Field

# 1. Connect to AIS agent
client = AISClient(
    agent_id='agent://example.com/my-client',
    agent_name='My Client'
)

await client.connect('http://localhost:8000')

# 2. Define schema
class CalculateArgs(BaseModel):
    operation: str = Field(description="Operation: add, subtract, multiply, divide")
    a: float = Field(description="First number")
    b: float = Field(description="Second number")

# 3. Create production-grade tool
calculator_tool = create_enhanced_ais_tool(EnhancedAISToolConfig(
    client=client,
    capability='calculate',
    args_schema=CalculateArgs,
    retry=RetryConfig(max_attempts=3),
    circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
    cache=True
))

# 4. Use in LangGraph
model = ChatOpenAI(model='gpt-4o-mini')
agent = create_react_agent(model, [calculator_tool])

# 5. Run!
result = await agent.ainvoke({
    'messages': [{'role': 'user', 'content': 'What is 42 times 17?'}]
})
```

---

## 🎓 Examples

### Simple Tool

```python
from ais_langchain import create_ais_tool

# Basic tool (no resilience features)
simple_tool = create_ais_tool(
    client=client,
    capability='greet'
)
```

### Production-Grade Tool

```python
from ais_langchain import (
    create_enhanced_ais_tool,
    EnhancedAISToolConfig,
    Logger,
    LoggerConfig,
    LogLevel,
    MetricsCollector,
    RetryConfig,
    CircuitBreakerConfig,
)

logger = Logger.get_instance_sync(LoggerConfig(level=LogLevel.INFO, pretty=True))
metrics = MetricsCollector()

production_tool = create_enhanced_ais_tool(EnhancedAISToolConfig(
    client=client,
    capability='process_data',
    retry=RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        backoff_multiplier=2.0
    ),
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,
        reset_timeout=30.0
    ),
    cache=True,
    cache_ttl=60.0,
    logger=logger,
    metrics=metrics
))
```

### Multi-Agent Management

```python
from ais_langchain import ManagedAISTools

# Create managed tools for multiple agents
managed = ManagedAISTools(client)

tools = managed.create_all_tools(
    retry=RetryConfig(max_attempts=3),
    circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
    cache=True,
    schemas={
        'calculate': CalculateArgs,
        'process_text': ProcessTextArgs
    }
)

# Get diagnostics
health = await managed.get_health()
metrics = managed.get_metrics()
diagnostics = await managed.get_diagnostics()
```

---

## 📊 Performance

### Caching Impact

```
Without caching:
- Average latency: ~800ms per call
- Network overhead: High

With caching (60s TTL):
- First call: ~800ms
- Cached calls: ~5ms
- Speedup: 160x ⚡
```

### Resilience Impact

```
Without retry/circuit breaker:
- Transient failures → errors
- Cascading failures possible
- Manual recovery needed

With retry + circuit breaker:
- 95%+ success rate with network issues
- Automatic recovery
- Prevents cascade failures
- Self-healing system ✨
```

---

## 🏗️ Architecture

### Tool Adapter

Converts AIS capabilities into LangChain tools:

```
AIS Agent                LangChain
   │                        │
   ├─ capability_1  ─→  Tool 1
   ├─ capability_2  ─→  Tool 2
   └─ capability_3  ─→  Tool 3
```

### Resilience Layers

```
LangGraph Request
    │
    ├─→ Response Cache (optional)
    │   ├─ Hit → Return cached
    │   └─ Miss → Continue
    │
    ├─→ Circuit Breaker
    │   ├─ OPEN → Fail fast
    │   ├─ HALF_OPEN → Test
    │   └─ CLOSED → Continue
    │
    ├─→ Retry Logic
    │   ├─ Success → Return
    │   └─ Failure → Retry with backoff
    │
    └─→ AIS Agent
        └─ Execute capability
```

---

## 📚 API Reference

### Core Functions

#### `create_ais_tool()`

Create a basic LangChain tool from an AIS capability.

```python
def create_ais_tool(
    client: AISClient,
    capability: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    args_schema: Optional[Type[BaseModel]] = None,
    timeout: Optional[float] = None,
) -> StructuredTool
```

#### `create_enhanced_ais_tool()`

Create a production-grade tool with resilience features.

```python
@dataclass
class EnhancedAISToolConfig:
    client: AISClient
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
```

#### `ManagedAISTools`

Manage multiple tools with shared infrastructure.

```python
managed = ManagedAISTools(
    client,
    logger=logger,
    metrics=metrics,
    cache=cache,
    cache_ttl=60.0
)

# Create all tools
tools = managed.create_all_tools(
    retry=RetryConfig(...),
    circuit_breaker=CircuitBreakerConfig(...),
    cache=True
)

# Get diagnostics
health = await managed.get_health()
metrics = managed.get_metrics()
diagnostics = await managed.get_diagnostics()
```

### Resilience Patterns

#### `with_retry()`

Execute function with retry logic.

```python
result = await with_retry(
    lambda: client.call('capability', params),
    RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        backoff_multiplier=2.0,
        jitter=0.1
    )
)
```

#### `CircuitBreaker`

Implement circuit breaker pattern.

```python
breaker = CircuitBreaker(CircuitBreakerConfig(
    failure_threshold=5,
    reset_timeout=30.0,
    on_open=lambda: print('Circuit OPEN'),
    on_close=lambda: print('Circuit CLOSED')
))

result = await breaker.execute(lambda: some_function())
```

#### `ResponseCache`

Cache responses.

```python
cache = ResponseCache(ttl=60.0)

cached = await cache.get('capability', params)
if not cached:
    result = await client.call('capability', params)
    await cache.set('capability', params, result)
```

### Observability

#### `Logger`

Structured logging.

```python
logger = Logger.get_instance_sync(LoggerConfig(
    level=LogLevel.INFO,
    pretty=True
))

logger.debug('Message', {'context': 'data'})
logger.info('Message', {'context': 'data'})
logger.warn('Message', {'context': 'data'})
logger.error('Message', error, {'context': 'data'})
```

#### `MetricsCollector`

Collect performance metrics.

```python
metrics = MetricsCollector()

metrics.increment_counter_sync('requests_total', 1, {'endpoint': '/api'})
metrics.record_histogram_sync('request_duration_ms', 245, {'endpoint': '/api'})
metrics.set_gauge_sync('active_connections', 10)

stats = metrics.get_histogram_stats('request_duration_ms')
print(stats['p95'])  # 95th percentile
```

#### `HealthChecker`

Monitor health.

```python
health = HealthChecker()

async def check_database():
    connected = await db.ping()
    return {
        'status': HealthStatus.HEALTHY if connected else HealthStatus.UNHEALTHY,
        'message': 'DB down' if not connected else 'DB connected'
    }

health.register('database', check_database)

result = await health.check()
print(result.status)  # HEALTHY | DEGRADED | UNHEALTHY
```

---

## 🎯 Use Cases

### 1. **Multi-Framework Integration**

LangChain agents calling AutoGPT, CrewAI, or custom agents:

```python
# LangChain → AIS → Any Agent Framework
autogpt_tool = create_enhanced_ais_tool(EnhancedAISToolConfig(
    client=autogpt_client,
    capability='research',
    retry=RetryConfig(max_attempts=3),
    cache=True
))

crewai_tool = create_enhanced_ais_tool(EnhancedAISToolConfig(
    client=crewai_client,
    capability='analyze',
    retry=RetryConfig(max_attempts=3),
    cache=True
))

agent = create_react_agent(model, [autogpt_tool, crewai_tool])
```

### 2. **Microservices for AI**

Each capability is an independent service:

```python
math_client = AISClient(...)
await math_client.connect('http://nlp-service:8001')

vision_client = AISClient(...)
await vision_client.connect('http://vision-service:8002')

speech_client = AISClient(...)
await speech_client.connect('http://speech-service:8003')
```

---

## 🏆 Production Checklist

Before deploying to production:

- ✅ Configure retry logic for your use case
- ✅ Set appropriate circuit breaker thresholds
- ✅ Enable caching for read-heavy workloads
- ✅ Set up health checks
- ✅ Monitor performance metrics
- ✅ Configure structured logging
- ✅ Set connection pool sizes
- ✅ Configure timeouts appropriately
- ✅ Test failure scenarios
- ✅ Set up alerting

---

## 🆘 Troubleshooting

### Common Issues

**"Cannot connect to AIS agent"**
```bash
# Make sure agent is running
curl http://localhost:8000/health
```

**"Circuit breaker is OPEN"**
```python
# Reset manually or wait for timeout
await managed_tools.reset_circuit_breakers()
```

**"Cache hit rate is low"**
```python
# Check stats
stats = cache.get_stats()
print(stats)
```

---

## 📝 License

Apache-2.0 - See [LICENSE](LICENSE) for details

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🔗 Links

- **PyPI:** https://pypi.org/project/ais-langchain/
- **GitHub:** https://github.com/ais-protocol/ais-langchain-python
- **AIS Protocol:** https://github.com/ais-protocol/ais-python
- **LangChain:** https://python.langchain.com/

---

## 🎉 Built for LangChain

This integration was built with ❤️ as a gift to the LangChain community.

**Let's make multi-agent AI interoperable!** 🚀
