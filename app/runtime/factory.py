from app.core.config import settings
from app.core.lifecycle import register_resource
from app.integrations.n8n import N8NWebhookAdapter
from app.persistence.database import AsyncpgDatabase
from app.persistence.postgres_stores import PostgresExecutionStore
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.service import IntegrationRuntime
from app.runtime.store import ExecutionStore, InMemoryExecutionStore


def build_execution_store() -> ExecutionStore:
    backend = settings.runtime_backend.lower().strip()
    if backend == "memory":
        return InMemoryExecutionStore()
    if backend == "postgres":
        database = register_resource(AsyncpgDatabase.from_settings())
        return PostgresExecutionStore(database)
    raise RuntimeError(f"Unsupported runtime backend: {backend}")


def build_connector_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    if settings.n8n_base_url:
        registry.register("n8n", N8NWebhookAdapter())
    return registry


def build_runtime() -> IntegrationRuntime:
    return IntegrationRuntime(
        registry=build_connector_registry(),
        store=build_execution_store(),
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
