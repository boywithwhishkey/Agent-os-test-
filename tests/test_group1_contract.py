import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationRequest, IntegrationResult
from app.runtime.circuit_breaker import CircuitBreaker
from app.runtime.models import ExecutionStatus, RuntimeRequest
from app.runtime.rate_limit import SlidingWindowRateLimiter
from app.runtime.registry import ConnectorRegistry
from app.runtime.service import IntegrationRuntime
from app.runtime.store import InMemoryExecutionStore

client = TestClient(__import__("app.main", fromlist=["app"]).app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


def test_health_is_public_and_returns_correlation_id():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"]


def test_invalid_and_missing_authentication_are_rejected(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "test-api-key")

    missing = client.get("/api/v1/tools")
    invalid = client.get("/api/v1/tools", headers={"X-API-Key": "wrong"})
    valid = client.get("/api/v1/tools", headers=AUTH_HEADERS)

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert valid.status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/v1/tasks"),
        ("GET", "/api/v1/tools"),
        ("POST", "/api/v1/memory/search"),
        ("GET", "/api/v1/workflows/runs/missing"),
        ("GET", "/api/v1/runtime/executions/missing"),
        ("POST", "/api/v1/autonomous/run"),
        ("POST", "/api/v1/integrations/execute"),
    ],
)
def test_operational_endpoints_require_authentication(method, path):
    assert client.request(method, path).status_code == 401


def test_incoming_correlation_id_is_returned():
    correlation_id = "request-123"

    response = client.get("/health", headers={"X-Correlation-ID": correlation_id})

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id


def test_invalid_incoming_correlation_id_is_replaced():
    response = client.get("/health", headers={"X-Correlation-ID": "bad value"})

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] != "bad value"


class RaisingAdapter(IntegrationAdapter):
    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        raise httpx.ConnectError("upstream unavailable")


class HangingAdapter(IntegrationAdapter):
    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        await asyncio.sleep(1)
        return IntegrationResult(
            provider="n8n",
            workflow=request.workflow,
            success=True,
        )


def make_runtime(adapter):
    registry = ConnectorRegistry()
    registry.register("n8n", adapter)
    return IntegrationRuntime(
        registry=registry,
        store=InMemoryExecutionStore(),
        circuit_breaker=CircuitBreaker(3, 60),
        rate_limiter=SlidingWindowRateLimiter(100, 60),
        backoff_base_seconds=0,
    )


@pytest.mark.asyncio
async def test_runtime_adapter_exception_becomes_failed_execution():
    execution = await make_runtime(RaisingAdapter()).execute(
        RuntimeRequest(provider="n8n", workflow="notify", max_retries=0)
    )

    assert execution.status == ExecutionStatus.FAILED
    assert execution.error == "Integration adapter failed: ConnectError"


@pytest.mark.asyncio
async def test_runtime_timeout_becomes_failed_execution():
    execution = await make_runtime(HangingAdapter()).execute(
        RuntimeRequest(provider="n8n", workflow="notify", timeout_seconds=0.01, max_retries=0)
    )

    assert execution.status == ExecutionStatus.FAILED
    assert execution.error == "Integration execution timed out"


@pytest.mark.asyncio
async def test_runtime_generates_and_propagates_correlation_id():
    class CapturingAdapter(IntegrationAdapter):
        async def execute(self, request: IntegrationRequest) -> IntegrationResult:
            assert request.correlation_id
            return IntegrationResult(
                provider="n8n",
                workflow=request.workflow,
                success=True,
                correlation_id=request.correlation_id,
            )

    execution = await make_runtime(CapturingAdapter()).execute(
        RuntimeRequest(provider="n8n", workflow="notify")
    )

    assert execution.status == ExecutionStatus.SUCCEEDED
    assert execution.correlation_id


def test_default_mock_autonomous_execution_is_deterministic():
    first = client.post(
        "/api/v1/autonomous/run",
        headers=AUTH_HEADERS,
        json={"objective": "Build a deterministic test plan"},
    )
    second = client.post(
        "/api/v1/autonomous/run",
        headers=AUTH_HEADERS,
        json={"objective": "Build a deterministic test plan"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert len(first.json()["plan"]["jobs"]) == 3