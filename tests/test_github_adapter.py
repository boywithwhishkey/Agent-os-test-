import httpx
import pytest

from app.core.config import settings
from app.integrations.github import GitHubOAuthAdapter
from app.integrations.models import IntegrationRequest
from app.integrations.oauth.store import OAuthConnectionStore


@pytest.mark.asyncio
async def test_github_adapter_reports_not_authorized_when_no_token():
    adapter = GitHubOAuthAdapter(connection_store=OAuthConnectionStore())
    connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "authorize" in (error or "").lower()


@pytest.mark.asyncio
async def test_github_adapter_verifies_stored_token():
    store = OAuthConnectionStore()
    store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer gho_test"
        assert str(request.url) == "https://api.github.com/user"
        return httpx.Response(200, json={"login": "octocat"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubOAuthAdapter(connection_store=store, client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_github_adapter_reports_revoked_token():
    store = OAuthConnectionStore()
    store.record_success("github", access_token="gho_revoked", token_type="bearer", scope="repo")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubOAuthAdapter(connection_store=store, client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "401" in (error or "")


@pytest.mark.asyncio
async def test_github_adapter_refreshes_once_after_expired_token(monkeypatch):
    monkeypatch.setattr(settings, "github_oauth_client_id", "client-123")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret-456")
    store = OAuthConnectionStore()
    store.record_success(
        "github",
        access_token="gho_expired",
        refresh_token="refresh-old",
        token_type="bearer",
        scope="repo",
    )
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url == "https://api.github.com/user":
            if request.headers["Authorization"] == "Bearer gho_expired":
                return httpx.Response(401, json={"message": "expired"})
            assert request.headers["Authorization"] == "Bearer gho_refreshed"
            return httpx.Response(200, json={"login": "octocat"})
        assert request.url == "https://github.com/login/oauth/access_token"
        return httpx.Response(200, json={"access_token": "gho_refreshed", "expires_in": 3600})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubOAuthAdapter(connection_store=store, client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is True
    assert error is None
    assert calls == [
        "https://api.github.com/user",
        "https://github.com/login/oauth/access_token",
        "https://api.github.com/user",
    ]
    assert store.get("github").access_token == "gho_refreshed"


@pytest.mark.asyncio
async def test_github_adapter_execute_is_unsupported():
    adapter = GitHubOAuthAdapter(connection_store=OAuthConnectionStore())
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False
