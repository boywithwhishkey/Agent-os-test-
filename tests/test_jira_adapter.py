from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.jira import JiraOAuthAdapter
from app.integrations.oauth.store import OAuthConnectionStore


def _store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        "jira", access_token="jira-access-token", token_type="Bearer", scope="read:jira-work"
    )
    return store


@pytest.mark.anyio
async def test_jira_identity_uses_fixed_cloud_api_and_bearer_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url == "https://api.atlassian.com/ex/jira/cloud-123/rest/api/3/myself"
        assert request.headers["authorization"] == "Bearer jira-access-token"
        return httpx.Response(200, json={"accountId": "acct-1", "displayName": "Demo"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await JiraOAuthAdapter(
            cloud_id="cloud-123", connection_store=_store(), client=client
        ).run_capability("identity.account.read", {})
    finally:
        await client.aclose()

    assert result["accountId"] == "acct-1"


@pytest.mark.anyio
async def test_jira_issue_list_posts_bounded_jql() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ex/jira/cloud-123/rest/api/3/search/jql"
        assert request.headers["authorization"] == "Bearer jira-access-token"
        assert json.loads(request.content) == {
            "jql": "project = THYNACT ORDER BY updated DESC",
            "maxResults": 7,
            "fields": ["summary", "status", "issuetype", "project"],
        }
        return httpx.Response(200, json={"issues": [{"key": "THY-1"}], "isLast": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await JiraOAuthAdapter(
            cloud_id="cloud-123", connection_store=_store(), client=client
        ).run_capability(
            "tracker.issue.list",
            {"jql": "project = THYNACT ORDER BY updated DESC", "max_results": 7},
        )
    finally:
        await client.aclose()

    assert result["issues"] == [{"key": "THY-1"}]


@pytest.mark.anyio
async def test_jira_issue_create_builds_bounded_adf_payload() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/issue")
        assert json.loads(request.content) == {
            "fields": {
                "project": {"key": "THY"},
                "summary": "Ship connectors",
                "issuetype": {"name": "Task"},
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "First line"}],
                        },
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Second line"}],
                        },
                    ],
                },
            }
        }
        return httpx.Response(201, json={"id": "10001", "key": "THY-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await JiraOAuthAdapter(
            cloud_id="cloud-123", connection_store=_store(), client=client
        ).run_capability(
            "tracker.issue.create",
            {"project_key": "THY", "summary": "Ship connectors", "description": "First line\nSecond line"},
        )
    finally:
        await client.aclose()

    assert result == {"id": "10001", "key": "THY-1"}


@pytest.mark.anyio
async def test_jira_issue_update_uses_fixed_issue_key_and_handles_204() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path.endswith("/issue/THY-1")
        assert json.loads(request.content) == {"fields": {"summary": "Updated summary"}}
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await JiraOAuthAdapter(
            cloud_id="cloud-123", connection_store=_store(), client=client
        ).run_capability("tracker.issue.update", {"issue_key": "THY-1", "summary": "Updated summary"})
    finally:
        await client.aclose()

    assert result == {"provider": "jira", "issue_key": "THY-1", "status_code": 204}


def test_jira_issue_mutations_validate_identifiers_and_fields() -> None:
    adapter = JiraOAuthAdapter(cloud_id="cloud-123", connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match="project key"):
        adapter._project_key({"project_key": "THY/NO"})
    with pytest.raises(ValueError, match="issue key"):
        adapter._issue_key({"issue_key": "../secret"})
    with pytest.raises(ValueError, match="summary"):
        adapter._summary({"summary": ""})


@pytest.mark.anyio
async def test_jira_unauthorized_response_is_secret_safe() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_token"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        connected, _, error = await JiraOAuthAdapter(
            cloud_id="cloud-123", connection_store=_store(), client=client
        ).test_connection()
    finally:
        await client.aclose()

    assert connected is False
    assert error == "Jira rejected the stored token (HTTP 401) — authorize again"
    assert "jira-access-token" not in error


def test_jira_requires_cloud_id_and_bounds_inputs() -> None:
    with pytest.raises(RuntimeError, match="JIRA_CLOUD_ID"):
        JiraOAuthAdapter(connection_store=OAuthConnectionStore())

    adapter = JiraOAuthAdapter(cloud_id="cloud-123", connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match="between 1 and 100"):
        adapter._max_results({"max_results": 101})
    with pytest.raises(ValueError, match="at most 2000"):
        adapter._jql({"jql": "x" * 2001})
