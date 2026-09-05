import json

import httpx
import pytest

from app.core.config import settings
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
async def test_cloudflare_identity_and_dns_reads_use_fixed_zone_routes():
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.url.query.decode()))
        if request.url.path == "/client/v4/user":
            return httpx.Response(200, json={"success": True, "result": {"id": "user-1"}})
        if request.url.path == "/client/v4/zones":
            return httpx.Response(
                200,
                json={"success": True, "result": [{"id": "zone123", "name": "example.com"}]},
            )
        return httpx.Response(
            200,
            json={"success": True, "result": [{"type": "A", "name": "example.com"}]},
        )

    async with _client(handler) as client:
        adapter = CloudflareAdapter(api_token="cf-test", client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        dns = await adapter.run_capability(
            "cloud.dns.read", {"zone_name": "example.com.", "max_results": 10}
        )

    assert identity["result"]["id"] == "user-1"
    assert dns["zone"]["id"] == "zone123"
    assert dns["records"]["result"][0]["type"] == "A"
    assert seen == [
        ("GET", "/client/v4/user", ""),
        ("GET", "/client/v4/zones", "name=example.com&per_page=5&page=1"),
        ("GET", "/client/v4/zones/zone123/dns_records", "per_page=10&page=1"),
    ]


def test_cloudflare_zone_name_is_strictly_validated():
    with pytest.raises(ValueError, match="zone_name"):
        CloudflareAdapter._zone_name({"zone_name": "http://example.com"})


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
async def test_render_service_read_and_deploy_use_fixed_governed_endpoints():
    seen: list[tuple[str, str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, body))
        if request.method == "GET":
            return httpx.Response(200, json=[{"service": {"id": "srv-123"}}])
        return httpx.Response(202, json={"deploy": {"id": "dep-1"}})

    async with _client(handler) as client:
        adapter = RenderAdapter(api_key="rnd-test", service_id="srv-123", client=client)
        services = await adapter.run_capability("cloud.service.read", {"max_results": 10})
        deploy = await adapter.run_capability(
            "cloud.deploy.trigger",
            {
                "service_id": "srv-123",
                "commit_id": "0123456789abcdef0123456789abcdef01234567",
                "clear_cache": True,
            },
        )

    assert services == [{"service": {"id": "srv-123"}}]
    assert deploy == {"deploy": {"id": "dep-1"}}
    assert seen == [
        ("GET", "/v1/services", None),
        (
            "POST",
            "/v1/services/srv-123/deploys",
            {
                "clearCache": "clear",
                "deployMode": "build_and_deploy",
                "commitId": "0123456789abcdef0123456789abcdef01234567",
            },
        ),
    ]


def test_render_deploy_arguments_are_strictly_validated(monkeypatch):
    monkeypatch.setattr(settings, "render_service_id", None)
    with pytest.raises(ValueError, match="service_id"):
        RenderAdapter._deploy_payload({})
    with pytest.raises(ValueError, match="deploy_mode"):
        RenderAdapter._deploy_payload({"service_id": "srv-1", "deploy_mode": "production"})
    with pytest.raises(ValueError, match="hexadecimal"):
        RenderAdapter._deploy_payload({"service_id": "srv-1", "commit_id": "not-a-sha"})


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
