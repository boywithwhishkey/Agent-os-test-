from app.core.config import settings
from app.integrations.n8n import N8NWebhookAdapter
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.service import IntegrationRuntime
from app.runtime.store import InMemoryExecutionStore


def build_runtime() -> IntegrationRuntime:
    registry = ConnectorRegistry()
    if settings.n8n_base_url:
        registry.register("n8n", N8NWebhookAdapter())
    return IntegrationRuntime(
        registry=registry,
        store=InMemoryExecutionStore(),
        circuit_breaker=CircuitBreaker(
            settings.circuit_failures,
            settings.circuit_recovery_seconds,
        ),
        rate_limiter=SlidingWindowRateLimiter(
            settings.integration_rate_limit,
            settings.integration_rate_window,
        ),
        backoff_base_seconds=settings.retry_backoff_base,
    )
