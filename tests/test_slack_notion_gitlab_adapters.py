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


@pytest.mark.asyncio
async def test_notion_adapter_searches_and_reads_pages_with_fixed_routes():
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret_notion", token_type="bearer", scope=None)
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, str(request.url)))
        assert request.headers["Authorization"] == "Bearer secret_notion"
        assert request.headers["Notion-Version"] == "2022-06-28"
        if request.url.path.endswith("/search"):
            assert json.loads(request.content) == {
                "page_size": 10,
                "filter": {"property": "object", "value": "page"},
                "query": "roadmap",
                "start_cursor": "next-page",
            }
            return httpx.Response(200, json={"results": [{"id": "page-1"}], "has_more": False})
        return httpx.Response(200, json={"id": "11111111-1111-1111-1111-111111111111", "object": "page"})

    async with _client(handler) as client:
        adapter = NotionOAuthAdapter(connection_store=store, client=client)
        search = await adapter.run_capability(
            "docs.page.read", {"query": "roadmap", "limit": 10, "cursor": "next-page"}
        )
        page = await adapter.run_capability(
            "docs.page.read", {"page_id": "11111111-1111-1111-1111-111111111111"}
        )

    assert search["results"] == [{"id": "page-1"}]
    assert page["object"] == "page"
    assert seen == [
        ("POST", "https://api.notion.com/v1/search"),
        ("GET", "https://api.notion.com/v1/pages/11111111-1111-1111-1111-111111111111"),
    ]


@pytest.mark.asyncio
async def test_notion_adapter_creates_a_bounded_page_under_a_fixed_parent():
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret_notion", token_type="bearer", scope=None)
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["version"] = request.headers["Notion-Version"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "page-new", "object": "page"})

    async with _client(handler) as client:
        adapter = NotionOAuthAdapter(connection_store=store, client=client)
        result = await adapter.run_capability(
            "docs.page.write",
            {
                "parent_page_id": "11111111-1111-1111-1111-111111111111",
                "title": "Release notes",
                "content": "Shipped the connector update.",
            },
        )

    assert result == {"id": "page-new", "object": "page"}
    assert seen == {
        "method": "POST",
        "url": "https://api.notion.com/v1/pages",
        "auth": "Bearer secret_notion",
        "version": "2022-06-28",
        "body": {
            "parent": {"page_id": "11111111-1111-1111-1111-111111111111"},
            "properties": {
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": "Release notes"}}
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Shipped the connector update."},
                            }
                        ]
                    },
                }
            ],
        },
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"parent_page_id": "bad", "title": "x"}, "Notion page id"),
        (
            {
                "parent_page_id": "11111111-1111-1111-1111-111111111111",
                "title": "",
            },
            "title",
        ),
    ],
)
def test_notion_page_write_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        NotionOAuthAdapter._page_write_payload(arguments)


@pytest.mark.asyncio
async def test_notion_adapter_rejects_invalid_page_id():
    adapter = NotionOAuthAdapter(connection_store=OAuthConnectionStore())

    with pytest.raises(ValueError, match="Notion page id"):
        await adapter.run_capability("docs.page.read", {"page_id": "../../secret"})


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
