from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings
from app.integrations.factory import is_provider_configured
from app.integrations.microsoft_todo import MicrosoftTodoOAuthAdapter
from app.integrations.models import IntegrationProvider
from app.integrations.oauth.store import OAuthConnectionStore


def _connected_store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        IntegrationProvider.MICROSOFT_TODO.value,
        access_token="microsoft-access-token",
        refresh_token="microsoft-refresh-token",
        token_type="Bearer",
        scope="User.Read Tasks.ReadWrite",
    )
    return store


def test_microsoft_todo_uses_shared_microsoft_oauth_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "microsoft_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "microsoft_oauth_client_secret", "client-secret")
    assert is_provider_configured(IntegrationProvider.MICROSOFT_TODO) is True


@pytest.mark.anyio
async def test_microsoft_todo_identity_and_tasks_use_graph_contract() -> None:
    seen: list[tuple[str, str, dict[str, str], dict | None]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, dict(request.headers), body))
        if request.url.path == "/v1.0/me":
            return httpx.Response(200, json={"id": "user-1", "displayName": "Nikhil"})
        if request.method == "GET":
            return httpx.Response(200, json={"value": [{"id": "task-1", "title": "Inbox"}]})
        return httpx.Response(201, json={"id": "task-2", "title": "Ship THYNACT"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = MicrosoftTodoOAuthAdapter(connection_store=_connected_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        listed = await adapter.run_capability(
            "productivity.task.list", {"tasklist_id": "list-1", "limit": 10}
        )
        created = await adapter.run_capability(
            "productivity.task.create",
            {"tasklist_id": "list-1", "title": "Ship THYNACT", "body": "Release checklist"},
        )
    finally:
        await client.aclose()

    assert identity["displayName"] == "Nikhil"
    assert listed["value"][0]["id"] == "task-1"
    assert created == {"id": "task-2", "title": "Ship THYNACT"}
    assert seen[0][0:2] == ("GET", "/v1.0/me")
    assert seen[0][2]["authorization"] == "Bearer microsoft-access-token"
    assert seen[1][0:2] == ("GET", "/v1.0/me/todo/lists/list-1/tasks")
    assert seen[1][3] is None
    assert seen[2][0:2] == ("POST", "/v1.0/me/todo/lists/list-1/tasks")
    assert seen[2][3] == {
        "title": "Ship THYNACT",
        "body": {"contentType": "text", "content": "Release checklist"},
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"tasklist_id": "", "title": "x"}, "tasklist_id"),
        ({"tasklist_id": "list-1", "title": ""}, "title"),
        ({"tasklist_id": "list-1", "title": "x", "due": "tomorrow"}, "ISO-8601"),
    ],
)
def test_microsoft_todo_arguments_are_bounded(arguments: dict[str, object], message: str) -> None:
    adapter = MicrosoftTodoOAuthAdapter(connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match=message):
        if "tasklist_id" in arguments and arguments.get("tasklist_id") in {"", "bad/id"}:
            adapter._identifier(arguments.get("tasklist_id"), "tasklist_id")
        else:
            adapter._task_payload(arguments)
