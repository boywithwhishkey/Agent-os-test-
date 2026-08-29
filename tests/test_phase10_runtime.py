import pytest
from fastapi.testclient import TestClient

from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.models import ExecutionStatus, RuntimeRequest
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.service import IntegrationRuntime
from app.runtime.store import InMemoryExecutionStore

class FakeAdapter(IntegrationAdapter):
    def __init__(self, failures_before_success=0):
        self.calls = 0
        self.failures_before_success = failures_before_success

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            return IntegrationResult(provider=IntegrationProvider.N8N,
                workflow=request.workflow, success=False, error="temporary failure")
        return IntegrationResult(provider=IntegrationProvider.N8N,
            workflow=request.workflow, success=True, status_code=200, data={"ok": True})

def make_runtime(adapter, rate_limit=100, threshold=3):
    registry = ConnectorRegistry()
    registry.register("n8n", adapter)
    return IntegrationRuntime(
        registry=registry, store=InMemoryExecutionStore(),
        circuit_breaker=CircuitBreaker(threshold, 60),
        rate_limiter=SlidingWindowRateLimiter(rate_limit, 60),
        backoff_base_seconds=0,
    )

@pytest.mark.asyncio
async def test_success_and_history():
    runtime = make_runtime(FakeAdapter())
    execution = await runtime.execute(RuntimeRequest(provider="n8n", workflow="notify"))
    assert execution.status == ExecutionStatus.SUCCEEDED
    assert (await runtime.store.get(execution.id)).data == {"ok": True}

@pytest.mark.asyncio
async def test_retries():
    adapter = FakeAdapter(2)
    runtime = make_runtime(adapter)
    execution = await runtime.execute(RuntimeRequest(provider="n8n", workflow="retry", max_retries=2))
    assert execution.status == ExecutionStatus.SUCCEEDED
    assert execution.attempts == 3

@pytest.mark.asyncio
async def test_idempotency():
    adapter = FakeAdapter()
    runtime = make_runtime(adapter)
    req = RuntimeRequest(provider="n8n", workflow="payment", idempotency_key="op-1")
    first = await runtime.execute(req)
    second = await runtime.execute(req)
    assert first.id == second.id
    assert adapter.calls == 1

@pytest.mark.asyncio
async def test_rate_limit():
    runtime = make_runtime(FakeAdapter(), rate_limit=1)
    assert (await runtime.execute(RuntimeRequest(provider="n8n", workflow="limited"))).status == ExecutionStatus.SUCCEEDED
    second = await runtime.execute(RuntimeRequest(provider="n8n", workflow="limited"))
    assert second.status == ExecutionStatus.REJECTED

@pytest.mark.asyncio
async def test_circuit_breaker():
    runtime = make_runtime(FakeAdapter(99), threshold=1)
    first = await runtime.execute(RuntimeRequest(provider="n8n", workflow="broken", max_retries=0))
    second = await runtime.execute(RuntimeRequest(provider="n8n", workflow="broken", max_retries=0))
    assert first.status == ExecutionStatus.FAILED
    assert second.status == ExecutionStatus.REJECTED
    assert second.error == "Circuit breaker is open"


@pytest.mark.asyncio
async def test_circuit_breaker_status_reports_open_after_failure():
    runtime = make_runtime(FakeAdapter(99), threshold=1)
    key = "n8n:broken"
    assert runtime.circuit_breaker.status(key)["state"] == "closed"

    await runtime.execute(RuntimeRequest(provider="n8n", workflow="broken", max_retries=0))

    status = runtime.circuit_breaker.status(key)
    assert status["state"] == "open"
    assert status["failures"] == 1
    assert status["recovers_in_seconds"] is not None


@pytest.mark.asyncio
async def test_rate_limit_usage_reports_consumed_slots():
    runtime = make_runtime(FakeAdapter(), rate_limit=5)
    key = "n8n:limited"
    assert runtime.rate_limiter.usage(key) == {"used": 0, "limit": 5, "window_seconds": 60}

    await runtime.execute(RuntimeRequest(provider="n8n", workflow="limited"))

    usage = runtime.rate_limiter.usage(key)
    assert usage["used"] == 1
    assert usage["limit"] == 5


def test_runtime_status_route_returns_closed_breaker_and_zero_usage():
    from app.main import app

    client = TestClient(app)
    response = client.get(
        "/api/v1/runtime/status",
        params={"provider": "n8n", "workflow": "some-fresh-workflow"},
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["circuit_breaker"]["state"] == "closed"
    assert body["rate_limit"]["used"] == 0
    assert body["rate_limit"]["limit"] > 0
