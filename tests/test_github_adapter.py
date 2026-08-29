import httpx
import pytest

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
async def test_github_adapter_execute_is_unsupported():
    adapter = GitHubOAuthAdapter(connection_store=OAuthConnectionStore())
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False
