import httpx
import pytest

from app.integrations.anthropic import AnthropicAdapter
from app.integrations.cloudflare import CloudflareAdapter
from app.integrations.gemini import GeminiAdapter
from app.integrations.models import IntegrationRequest
from app.integrations.openai import OpenAIAdapter
from app.integrations.render import RenderAdapter


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_openai_adapter_test_connection_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer sk-test"
        assert str(request.url).startswith("https://api.openai.com/v1/models")
        return httpx.Response(200, json={"data": []})

    async with _client(handler) as client:
        adapter = OpenAIAdapter(api_key="sk-test", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_openai_adapter_test_connection_rejects_bad_key():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid api key"})

    async with _client(handler) as client:
        adapter = OpenAIAdapter(api_key="sk-bad", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "401" in (error or "")


@pytest.mark.asyncio
async def test_openai_adapter_test_connection_timeout():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    async with _client(handler) as client:
        adapter = OpenAIAdapter(api_key="sk-test", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "timed out" in (error or "").lower()


@pytest.mark.asyncio
async def test_openai_adapter_execute_is_unsupported():
    adapter = OpenAIAdapter(api_key="sk-test")
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False
    assert result.error


@pytest.mark.asyncio
async def test_openai_adapter_requires_api_key():
    with pytest.raises(RuntimeError):
        OpenAIAdapter(api_key=None)


@pytest.mark.asyncio
async def test_anthropic_adapter_test_connection_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "sk-ant-test"
        assert request.headers["anthropic-version"]
        return httpx.Response(200, json={"data": []})

    async with _client(handler) as client:
        adapter = AnthropicAdapter(api_key="sk-ant-test", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is True
    assert error is None


@pytest.mark.asyncio
async def test_anthropic_adapter_test_connection_rejects_bad_key():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid"})

    async with _client(handler) as client:
        adapter = AnthropicAdapter(api_key="sk-ant-bad", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "401" in (error or "")


@pytest.mark.asyncio
async def test_cloudflare_adapter_test_connection_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer cf-test"
        return httpx.Response(200, json={"success": True, "result": {"status": "active"}})

    async with _client(handler) as client:
        adapter = CloudflareAdapter(api_token="cf-test", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is True
    assert error is None


@pytest.mark.asyncio
async def test_cloudflare_adapter_test_connection_rejects_invalid_token():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": False, "errors": [{"message": "invalid"}]})

    async with _client(handler) as client:
        adapter = CloudflareAdapter(api_token="cf-bad", client=client)
        connected, _, _error = await adapter.test_connection()

    assert connected is False


@pytest.mark.asyncio
async def test_render_adapter_test_connection_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer rnd-test"
        return httpx.Response(200, json=[{"owner": {"id": "usr-1"}}])

    async with _client(handler) as client:
        adapter = RenderAdapter(api_key="rnd-test", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is True
    assert error is None


@pytest.mark.asyncio
async def test_render_adapter_test_connection_network_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with _client(handler) as client:
        adapter = RenderAdapter(api_key="rnd-test", client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "ConnectError" in (error or "")


@pytest.mark.asyncio
async def test_gemini_adapter_test_connection_success():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["key"] == "gm-test"
        return httpx.Response(200, json={"models": []})

    async with _client(handler) as client:
        adapter = GeminiAdapter(api_key="gm-test", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is True
    assert error is None


@pytest.mark.asyncio
async def test_gemini_adapter_test_connection_rejects_bad_key():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "API key not valid"})

    async with _client(handler) as client:
        adapter = GeminiAdapter(api_key="gm-bad", client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "400" in (error or "")
