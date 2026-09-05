import httpx
import pytest

from app.integrations.github import GitHubOAuthAdapter
from app.integrations.models import IntegrationRequest
from app.integrations.oauth.store import InMemoryOAuthConnectionStore


@pytest.mark.asyncio
async def test_github_adapter_reports_not_authorized_when_no_token():
    adapter = GitHubOAuthAdapter(connection_store=InMemoryOAuthConnectionStore())
    connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "authorize" in (error or "").lower()


@pytest.mark.asyncio
async def test_github_adapter_verifies_stored_token():
    store = InMemoryOAuthConnectionStore()
    await store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

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
    store = InMemoryOAuthConnectionStore()
    await store.record_success("github", access_token="gho_revoked", token_type="bearer", scope="repo")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubOAuthAdapter(connection_store=store, client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "401" in (error or "")


@pytest.mark.asyncio
async def test_github_adapter_execute_is_unsupported():
    adapter = GitHubOAuthAdapter(connection_store=InMemoryOAuthConnectionStore())
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False


@pytest.mark.asyncio
async def test_github_run_capability_lists_repos_with_only_the_safe_fields():
    store = InMemoryOAuthConnectionStore()
    await store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.github.com/user/repos?per_page=100"
        assert request.headers["Authorization"] == "Bearer gho_test"
        return httpx.Response(
            200,
            json=[
                {
                    "full_name": "octocat/hello-world",
                    "private": False,
                    "default_branch": "main",
                    "clone_url": "https://x:gho_test@github.com/octocat/hello-world.git",
                }
            ],
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubOAuthAdapter(connection_store=store, client=client)
        repos = await adapter.run_capability("repo.metadata.read", {})

    assert repos == [{"full_name": "octocat/hello-world", "private": False, "default_branch": "main"}]
    # GitHub's real response embeds a credentialed clone_url; only the three
    # named fields must survive into what an agent or an audit record sees.
    assert "gho_test" not in str(repos)


@pytest.mark.asyncio
async def test_github_run_capability_identity_read_matches_the_verify_call():
    store = InMemoryOAuthConnectionStore()
    await store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.github.com/user"
        return httpx.Response(200, json={"login": "octocat", "id": 1})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitHubOAuthAdapter(connection_store=store, client=client)
        identity = await adapter.run_capability("identity.account.read", {})

    assert identity["login"] == "octocat"


@pytest.mark.asyncio
async def test_github_run_capability_refuses_an_unwired_write_capability():
    from app.integrations.base import CapabilityNotWired

    store = InMemoryOAuthConnectionStore()
    await store.record_success("github", access_token="gho_test", token_type="bearer", scope="repo")
    adapter = GitHubOAuthAdapter(connection_store=store)

    with pytest.raises(CapabilityNotWired):
        await adapter.run_capability("repo.branch.merge", {})
