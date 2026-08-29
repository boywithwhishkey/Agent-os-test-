import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import phase9
from app.core.config import settings
from app.integrations.mcp.client import MCPHttpClient
from app.integrations.mcp.models import MCPAuthType, MCPServerCreate
from app.integrations.mcp.store import MCPServerStore
from app.main import app

client = TestClient(app)
AUTH = {"X-API-Key": "test-api-key"}


@pytest.fixture(autouse=True)
def _reset_mcp_store():
    phase9.mcp_store = MCPServerStore()
    yield
    phase9.mcp_store = MCPServerStore()


def _rpc_handler(responses: dict[str, dict]):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        method = payload["method"]
        if method in responses:
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, **responses[method]})
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"message": "Method not found"}})

    return handler


# --- MCPHttpClient ---


@pytest.mark.asyncio
async def test_mcp_client_discovers_capabilities():
    transport = httpx.MockTransport(
        _rpc_handler(
            {
                "initialize": {"result": {"protocolVersion": "2025-03-26"}},
                "tools/list": {"result": {"tools": [{"name": "search", "description": "Search the web"}]}},
                "resources/list": {"result": {"resources": []}},
            }
        )
    )
    async with httpx.AsyncClient(transport=transport) as http_client:
        mcp = MCPHttpClient(endpoint="https://mcp.example/rpc", client=http_client)
        connected, latency_ms, error, capabilities = await mcp.discover()

    assert connected is True
    assert latency_ms is not None
    assert error is None
    assert len(capabilities.tools) == 1
    assert capabilities.tools[0].name == "search"
    assert capabilities.tools[0].description == "Search the web"
    assert capabilities.prompts == []  # server didn't implement prompts/list — not a failure


@pytest.mark.asyncio
async def test_mcp_client_reports_initialize_failure():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"message": "unauthorized"}})
    )
    async with httpx.AsyncClient(transport=transport) as http_client:
        mcp = MCPHttpClient(endpoint="https://mcp.example/rpc", client=http_client)
        connected, latency_ms, error, capabilities = await mcp.discover()

    assert connected is False
    assert latency_ms is None
    assert error == "unauthorized"


@pytest.mark.asyncio
async def test_mcp_client_reports_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        mcp = MCPHttpClient(endpoint="https://mcp.example/rpc", client=http_client)
        connected, latency_ms, error, capabilities = await mcp.discover()

    assert connected is False
    assert "timed out" in (error or "").lower()


@pytest.mark.asyncio
async def test_mcp_client_reports_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        mcp = MCPHttpClient(endpoint="https://mcp.example/rpc", client=http_client)
        connected, latency_ms, error, capabilities = await mcp.discover()

    assert connected is False
    assert "ConnectError" in (error or "")


@pytest.mark.asyncio
async def test_mcp_client_sends_bearer_auth_header():
    seen_headers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        mcp = MCPHttpClient(
            endpoint="https://mcp.example/rpc",
            auth_type=MCPAuthType.BEARER,
            secret_value="s3cret",
            client=http_client,
        )
        await mcp.discover()

    assert seen_headers.get("authorization") == "Bearer s3cret"


# --- MCP API routes ---


def test_mcp_server_list_is_public():
    response = client.get("/api/v1/integrations/mcp/servers")
    assert response.status_code == 200
    assert response.json() == []


def test_creating_mcp_server_requires_auth():
    response = client.post(
        "/api/v1/integrations/mcp/servers",
        json={"name": "My MCP", "endpoint": "https://mcp.example/rpc"},
    )
    assert response.status_code == 401


def test_create_mcp_server_never_returns_secret():
    response = client.post(
        "/api/v1/integrations/mcp/servers",
        headers=AUTH,
        json={
            "name": "My MCP",
            "endpoint": "https://mcp.example/rpc",
            "auth_type": "bearer",
            "secret_value": "super-secret-token",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "secret_value" not in body
    assert "super-secret-token" not in json.dumps(body)
    assert body["has_secret"] is True

    listing = client.get("/api/v1/integrations/mcp/servers").json()
    assert "super-secret-token" not in json.dumps(listing)


def test_test_mcp_server_records_capabilities(monkeypatch):
    create = client.post(
        "/api/v1/integrations/mcp/servers",
        headers=AUTH,
        json={"name": "My MCP", "endpoint": "https://mcp.example/rpc"},
    ).json()

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def discover(self):
            from app.integrations.mcp.models import MCPCapabilities, MCPCapabilityItem

            return True, 12.3, None, MCPCapabilities(tools=[MCPCapabilityItem(name="search")])

    monkeypatch.setattr(phase9, "MCPHttpClient", FakeClient)

    response = client.post(f"/api/v1/integrations/mcp/servers/{create['id']}/test", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["capabilities"]["tools"][0]["name"] == "search"


def test_test_unknown_mcp_server_returns_404():
    response = client.post("/api/v1/integrations/mcp/servers/does-not-exist/test", headers=AUTH)
    assert response.status_code == 404


def test_delete_mcp_server_requires_auth_and_removes_it():
    create = client.post(
        "/api/v1/integrations/mcp/servers",
        headers=AUTH,
        json={"name": "Temp", "endpoint": "https://mcp.example/rpc"},
    ).json()

    unauth = client.delete(f"/api/v1/integrations/mcp/servers/{create['id']}")
    assert unauth.status_code == 401

    response = client.delete(f"/api/v1/integrations/mcp/servers/{create['id']}", headers=AUTH)
    assert response.status_code == 204

    listing = client.get("/api/v1/integrations/mcp/servers").json()
    assert all(item["id"] != create["id"] for item in listing)


def test_delete_unknown_mcp_server_returns_404():
    response = client.delete("/api/v1/integrations/mcp/servers/does-not-exist", headers=AUTH)
    assert response.status_code == 404
