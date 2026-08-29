import httpx
import pytest

from app.integrations.make import MakeWebhookAdapter
from app.integrations.models import IntegrationRequest


@pytest.mark.asyncio
async def test_make_adapter_execute_posts_workflow_label_and_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://hook.make.com/abc123"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MakeWebhookAdapter(webhook_url="https://hook.make.com/abc123", client=client)
        result = await adapter.execute(IntegrationRequest(workflow="deploy-notify", payload={"env": "prod"}))

    assert result.success is True
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_make_adapter_requires_webhook_url():
    with pytest.raises(RuntimeError):
        MakeWebhookAdapter(webhook_url="")


@pytest.mark.asyncio
async def test_make_adapter_supports_custom_auth_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Make-Token"] == "secret"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MakeWebhookAdapter(
            webhook_url="https://hook.make.com/abc123",
            auth_header="X-Make-Token",
            auth_value="secret",
            client=client,
        )
        result = await adapter.execute(IntegrationRequest(workflow="notify"))

    assert result.success is True


@pytest.mark.asyncio
async def test_make_adapter_failure_is_structured():
    transport = httpx.MockTransport(lambda request: httpx.Response(500, json={"message": "boom"}))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MakeWebhookAdapter(webhook_url="https://hook.make.com/abc123", client=client)
        result = await adapter.execute(IntegrationRequest(workflow="broken"))

    assert result.success is False
    assert "HTTP 500" in (result.error or "")


@pytest.mark.asyncio
async def test_make_adapter_test_connection_reports_reachable_host():
    transport = httpx.MockTransport(lambda request: httpx.Response(405))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MakeWebhookAdapter(webhook_url="https://hook.make.com/abc123", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_make_adapter_test_connection_reports_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = MakeWebhookAdapter(webhook_url="https://hook.make.com/abc123", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "timed out" in (error or "").lower()
