import os
from app.integrations.n8n import N8NWebhookAdapter
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.service import IntegrationRuntime
from app.runtime.store import InMemoryExecutionStore

def build_runtime() -> IntegrationRuntime:
    registry = ConnectorRegistry()
    if os.getenv("N8N_BASE_URL"):
        registry.register("n8n", N8NWebhookAdapter())
    return IntegrationRuntime(
        registry=registry,
        store=InMemoryExecutionStore(),
        circuit_breaker=CircuitBreaker(
            int(os.getenv("AGENT_OS_CIRCUIT_FAILURES", "3")),
            float(os.getenv("AGENT_OS_CIRCUIT_RECOVERY_SECONDS", "30")),
        ),
        rate_limiter=SlidingWindowRateLimiter(
            int(os.getenv("AGENT_OS_INTEGRATION_RATE_LIMIT", "60")),
            float(os.getenv("AGENT_OS_INTEGRATION_RATE_WINDOW", "60")),
        ),
        backoff_base_seconds=float(os.getenv("AGENT_OS_RETRY_BACKOFF_BASE", "0.25")),
    )
