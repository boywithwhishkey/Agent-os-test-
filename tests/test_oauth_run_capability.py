"""`run_capability` for the OAuth adapters that only wire identity-read so far
(GitLab beyond identity, Slack, Notion), plus the broker's distinction between
an OAuth app being registered and an account actually being connected.
"""

from __future__ import annotations

import httpx
import pytest

from app.integrations.base import CapabilityNotWired
from app.integrations.gitlab import GitLabOAuthAdapter
from app.integrations.notion import NotionOAuthAdapter
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.slack import SlackOAuthAdapter

pytestmark = pytest.mark.asyncio


async def test_gitlab_lists_projects_with_only_the_safe_fields():
    store = OAuthConnectionStore()
    store.record_success("gitlab", access_token="glpat-test", token_type="bearer", scope="api")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://gitlab.com/api/v4/projects?membership=true&per_page=100"
        return httpx.Response(
            200,
            json=[
                {
                    "path_with_namespace": "group/project",
                    "visibility": "private",
                    "default_branch": "main",
                    "runners_token": "should-never-appear",
                }
            ],
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = GitLabOAuthAdapter(connection_store=store, client=client)
        projects = await adapter.run_capability("repo.metadata.read", {})

    assert projects == [{"path_with_namespace": "group/project", "visibility": "private", "default_branch": "main"}]
    assert "runners_token" not in str(projects)
    assert "should-never-appear" not in str(projects)


async def test_gitlab_refuses_an_unwired_write_capability():
    store = OAuthConnectionStore()
    store.record_success("gitlab", access_token="glpat-test", token_type="bearer", scope="api")
    adapter = GitLabOAuthAdapter(connection_store=store)

    with pytest.raises(CapabilityNotWired):
        await adapter.run_capability("repo.issue.create", {})


async def test_slack_identity_read_is_wired():
    store = OAuthConnectionStore()
    store.record_success("slack", access_token="xoxb-test", token_type="bearer", scope="chat:write")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://slack.com/api/auth.test"
        return httpx.Response(200, json={"ok": True, "user": "botuser", "team": "T1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = SlackOAuthAdapter(connection_store=store, client=client)
        identity = await adapter.run_capability("identity.account.read", {})

    assert identity["ok"] is True


async def test_slack_chat_message_list_stays_unwired():
    """Deliberate: no channel-selection argument shape exists yet — wiring it
    would mean inventing one ahead of any real caller."""
    store = OAuthConnectionStore()
    store.record_success("slack", access_token="xoxb-test", token_type="bearer", scope="channels:history")
    adapter = SlackOAuthAdapter(connection_store=store)

    with pytest.raises(CapabilityNotWired):
        await adapter.run_capability("chat.message.list", {})


async def test_notion_identity_read_is_wired():
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret_test", token_type="bearer", scope=None)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.notion.com/v1/users/me"
        assert request.headers["Notion-Version"] == "2022-06-28"
        return httpx.Response(200, json={"id": "u1", "type": "bot"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = NotionOAuthAdapter(connection_store=store, client=client)
        identity = await adapter.run_capability("identity.account.read", {})

    assert identity["type"] == "bot"


async def test_notion_docs_page_read_stays_unwired_without_a_page_id():
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret_test", token_type="bearer", scope=None)
    adapter = NotionOAuthAdapter(connection_store=store)

    with pytest.raises(CapabilityNotWired):
        await adapter.run_capability("docs.page.read", {})
