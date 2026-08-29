import httpx
import pytest

from app.integrations.models import IntegrationRequest
from app.integrations.n8n import N8NWebhookAdapter
from app.workflows.integration_handler import run_integration_step


@pytest.mark.asyncio
async def test_n8n_webhook_adapter_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://n8n.example/webhook/send-email"
        assert request.headers["X-Agent-OS-Correlation-ID"] == "abc-123"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(
            base_url="https://n8n.example",
            client=client,
        )
        result = await adapter.execute(
            IntegrationRequest(
                workflow="send-email",
                payload={"to": "user@example.com"},
                correlation_id="abc-123",
            )
        )

    assert result.success is True
    assert result.status_code == 200
    assert result.data == {"ok": True}


@pytest.mark.asyncio
async def test_n8n_webhook_adapter_supports_custom_auth_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Agent-Token"] == "secret"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(
            base_url="https://n8n.example",
            auth_header="X-Agent-Token",
            auth_value="secret",
            client=client,
        )
        result = await adapter.execute(
            IntegrationRequest(workflow="crm-sync")
        )

    assert result.success is True


@pytest.mark.asyncio
async def test_n8n_failure_is_structured():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500, json={"message": "boom"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(
            base_url="https://n8n.example",
            client=client,
        )
        result = await adapter.execute(
            IntegrationRequest(workflow="broken")
        )

    assert result.success is False
    assert result.status_code == 500
    assert "HTTP 500" in (result.error or "")


@pytest.mark.asyncio
async def test_n8n_test_connection_reports_reachable_host():
    transport = httpx.MockTransport(lambda request: httpx.Response(404))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(base_url="https://n8n.example", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None and latency_ms >= 0
    assert error is None


@pytest.mark.asyncio
async def test_n8n_test_connection_reports_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(base_url="https://n8n.example", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "timed out" in (error or "").lower()


@pytest.mark.asyncio
async def test_n8n_test_connection_reports_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(base_url="https://n8n.example", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "ConnectError" in (error or "")


@pytest.mark.asyncio
async def test_workflow_integration_handler_returns_data():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"execution": "done"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = N8NWebhookAdapter(
            base_url="https://n8n.example",
            client=client,
        )
        data = await run_integration_step(
            adapter=adapter,
            workflow="notify",
            payload={"message": "hello"},
        )

    assert data == {"execution": "done"}
