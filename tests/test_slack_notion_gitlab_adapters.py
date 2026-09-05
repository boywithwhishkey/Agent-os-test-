import json

import httpx
import pytest

from app.integrations.gitlab import GitLabOAuthAdapter
from app.integrations.models import IntegrationRequest
from app.integrations.notion import NotionOAuthAdapter
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.slack import SlackOAuthAdapter


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- Slack ---


@pytest.mark.asyncio
async def test_slack_adapter_reports_not_connected_when_no_token():
    adapter = SlackOAuthAdapter(connection_store=OAuthConnectionStore())
    connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "connect" in (error or "").lower()


@pytest.mark.asyncio
async def test_slack_adapter_verifies_stored_token():
    store = OAuthConnectionStore()
    store.record_success("slack", access_token="xoxb-test", token_type="bearer", scope="chat:write")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer xoxb-test"
        return httpx.Response(200, json={"ok": True, "team": "Acme"})

    async with _client(handler) as client:
        adapter = SlackOAuthAdapter(connection_store=store, client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_slack_adapter_detects_ok_false_despite_http_200():
    # Slack's Web API always answers HTTP 200 — failures are only visible in
    # the JSON body. A naive status-code check would wrongly report success.
    store = OAuthConnectionStore()
    store.record_success("slack", access_token="xoxb-revoked", token_type="bearer", scope="chat:write")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "error": "invalid_auth"})

    async with _client(handler) as client:
        adapter = SlackOAuthAdapter(connection_store=store, client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "invalid_auth" in (error or "")


@pytest.mark.asyncio
async def test_slack_adapter_posts_a_governed_message():
    store = OAuthConnectionStore()
    store.record_success("slack", access_token="xoxb-test", token_type="bearer", scope="chat:write")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://slack.com/api/chat.postMessage"
        assert request.headers["Authorization"] == "Bearer xoxb-test"
        assert json.loads(request.content) == {"channel": "C123", "text": "hello"}
        return httpx.Response(200, json={"ok": True, "channel": "C123", "ts": "123.456"})

    async with _client(handler) as client:
        adapter = SlackOAuthAdapter(connection_store=store, client=client)
        result = await adapter.run_capability("chat.message.send", {"channel": "C123", "text": "hello"})

    assert result == {"provider": "slack", "channel": "C123", "message_id": "123.456"}


@pytest.mark.asyncio
async def test_slack_adapter_lists_bounded_channel_messages():
    store = OAuthConnectionStore()
    store.record_success(
        "slack",
        access_token="xoxb-test",
        token_type="bearer",
        scope="chat:write channels:history",
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://slack.com/api/conversations.history?channel=C123&limit=20"
        assert request.headers["Authorization"] == "Bearer xoxb-test"
        return httpx.Response(
            200,
            json={
                "ok": True,
                "channel": "C123",
                "messages": [{"type": "message", "ts": "123.456", "text": "hello"}],
                "has_more": True,
                "response_metadata": {"next_cursor": "next-page"},
            },
        )

    async with _client(handler) as client:
        adapter = SlackOAuthAdapter(connection_store=store, client=client)
        result = await adapter.run_capability("chat.message.list", {"channel": "C123"})

    assert result == {
        "provider": "slack",
        "channel": "C123",
        "messages": [{"type": "message", "ts": "123.456", "text": "hello"}],
        "has_more": True,
        "next_cursor": "next-page",
    }


@pytest.mark.asyncio
async def test_slack_adapter_lists_allowlisted_channels_with_pagination():
    store = OAuthConnectionStore()
    store.record_success(
        "slack",
        access_token="xoxb-test",
        token_type="bearer",
        scope="channels:read groups:read im:read mpim:read",
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert (
            str(request.url)
            == "https://slack.com/api/conversations.list?limit=20&exclude_archived=true&types=public_channel%2Cprivate_channel&cursor=next-page"
        )
        assert request.headers["Authorization"] == "Bearer xoxb-test"
        return httpx.Response(
            200,
            json={
                "ok": True,
                "channels": [{"id": "C123", "name": "general", "is_channel": True}],
                "response_metadata": {"next_cursor": "final-page"},
            },
        )

    async with _client(handler) as client:
        adapter = SlackOAuthAdapter(connection_store=store, client=client)
        result = await adapter.run_capability(
            "chat.channel.list",
            {"types": "public_channel,private_channel", "cursor": "next-page"},
        )

    assert result == {
        "provider": "slack",
        "channels": [{"id": "C123", "name": "general", "is_channel": True}],
        "has_more": False,
        "next_cursor": "final-page",
    }


@pytest.mark.asyncio
async def test_slack_adapter_rejects_unknown_channel_type():
    adapter = SlackOAuthAdapter(connection_store=OAuthConnectionStore())

    with pytest.raises(ValueError, match="unsupported conversation type"):
        await adapter.run_capability("chat.channel.list", {"types": "public_channel,unknown"})


@pytest.mark.asyncio
async def test_slack_adapter_rejects_unbounded_message_list_limit():
    adapter = SlackOAuthAdapter(connection_store=OAuthConnectionStore())

    with pytest.raises(ValueError, match="between 1 and 100"):
        await adapter.run_capability("chat.message.list", {"channel": "C123", "limit": 101})


@pytest.mark.asyncio
async def test_slack_adapter_execute_is_unsupported():
    adapter = SlackOAuthAdapter(connection_store=OAuthConnectionStore())
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False


# --- Notion ---


@pytest.mark.asyncio
async def test_notion_adapter_verifies_stored_token_with_version_header():
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret_notion", token_type="bearer", scope=None)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret_notion"
        assert request.headers["Notion-Version"] == "2022-06-28"
        assert str(request.url) == "https://api.notion.com/v1/users/me"
        return httpx.Response(200, json={"id": "user-1"})

    async with _client(handler) as client:
        adapter = NotionOAuthAdapter(connection_store=store, client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_notion_adapter_reports_not_connected_when_no_token():
    adapter = NotionOAuthAdapter(connection_store=OAuthConnectionStore())
    connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "connect" in (error or "").lower()


@pytest.mark.asyncio
async def test_notion_adapter_reports_rejected_token():
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret_revoked", token_type="bearer", scope=None)

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "unauthorized"})

    async with _client(handler) as client:
        adapter = NotionOAuthAdapter(connection_store=store, client=client)
        connected, _, error = await adapter.test_connection()

    assert connected is False
    assert "401" in (error or "")


# --- GitLab ---


@pytest.mark.asyncio
async def test_gitlab_adapter_verifies_stored_token():
    store = OAuthConnectionStore()
    store.record_success("gitlab", access_token="glpat-test", token_type="bearer", scope="read_api")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer glpat-test"
        assert str(request.url) == "https://gitlab.com/api/v4/user"
        return httpx.Response(200, json={"username": "octocat"})

    async with _client(handler) as client:
        adapter = GitLabOAuthAdapter(connection_store=store, client=client)
        connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_gitlab_adapter_reads_project_metadata_and_repository_file():
    store = OAuthConnectionStore()
    store.record_success("gitlab", access_token="glpat-test", token_type="bearer", scope="read_api")
    seen: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        assert request.headers["Authorization"] == "Bearer glpat-test"
        if request.url.path.endswith("/repository/files/docs/README.md"):
            return httpx.Response(200, json={"file_name": "README.md", "encoding": "base64"})
        return httpx.Response(200, json={"path_with_namespace": "group/project", "visibility": "private"})

    async with _client(handler) as client:
        adapter = GitLabOAuthAdapter(connection_store=store, client=client)
        metadata = await adapter.run_capability("repo.metadata.read", {"project": "group/project"})
        content = await adapter.run_capability(
            "repo.content.read", {"project": "group/project", "path": "docs/README.md", "ref": "main"}
        )

    assert metadata["path_with_namespace"] == "group/project"
    assert content["file_name"] == "README.md"
    assert seen == [
        "https://gitlab.com/api/v4/projects/group%2Fproject",
        "https://gitlab.com/api/v4/projects/group%2Fproject/repository/files/docs%2FREADME.md?ref=main",
    ]


@pytest.mark.asyncio
async def test_gitlab_adapter_rejects_parent_traversal_in_project_path():
    store = OAuthConnectionStore()
    store.record_success("gitlab", access_token="glpat-test", token_type="bearer", scope="read_api")
    adapter = GitLabOAuthAdapter(connection_store=store)

    with pytest.raises(ValueError, match="safe GitLab project path"):
        await adapter.run_capability("repo.metadata.read", {"project": "group/../secret"})


@pytest.mark.asyncio
async def test_gitlab_adapter_execute_is_unsupported():
    adapter = GitLabOAuthAdapter(connection_store=OAuthConnectionStore())
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False
