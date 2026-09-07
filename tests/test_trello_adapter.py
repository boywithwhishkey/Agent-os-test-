from __future__ import annotations

import httpx
import pytest

from app.core.config import settings
from app.integrations.factory import is_provider_configured
from app.integrations.models import IntegrationProvider
from app.integrations.trello import TrelloAdapter


def _adapter(client: httpx.AsyncClient) -> TrelloAdapter:
    return TrelloAdapter(
        api_key="trello-api-key",
        token="trello-token",
        board_id="board123",
        list_id="list123",
        client=client,
    )


@pytest.mark.anyio
async def test_trello_identity_and_task_list_use_fixed_board_and_secret_query_auth():
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.url.query.decode()))
        if request.url.path.endswith("/members/me"):
            return httpx.Response(200, json={"id": "member-1", "fullName": "Nikhil"})
        return httpx.Response(200, json=[{"id": "card-1"}, {"id": "card-2"}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = _adapter(client)
        identity = await adapter.run_capability("identity.account.read", {})
        cards = await adapter.run_capability("productivity.task.list", {"limit": 1})

    assert identity == {"id": "member-1", "fullName": "Nikhil"}
    assert cards == {
        "provider": "trello",
        "cards": [{"id": "card-1"}],
        "truncated": True,
    }
    assert seen == [
        (
            "GET",
            "/1/members/me",
            "key=trello-api-key&token=trello-token&fields=id%2CfullName%2Cusername%2Curl",
        ),
        (
            "GET",
            "/1/boards/board123/cards",
            "key=trello-api-key&token=trello-token&fields=id%2Cname%2Cdesc%2Cdue%2CidList%2Curl&filter=open",
        ),
    ]


@pytest.mark.anyio
async def test_trello_task_create_uses_fixed_list_and_bounded_fields():
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        return httpx.Response(200, json={"id": "card-new", "name": "Ship it"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await _adapter(client).run_capability(
            "productivity.task.create",
            {
                "content": "Ship it",
                "description": "Release the connector",
                "due": "2026-09-08T10:00:00Z",
            },
        )

    assert result == {"id": "card-new", "name": "Ship it"}
    assert seen == {
        "method": "POST",
        "path": "/1/cards",
        "query": (
            "key=trello-api-key&token=trello-token&idList=list123&name=Ship+it&pos=top"
            "&desc=Release+the+connector&due=2026-09-08T10%3A00%3A00Z"
        ),
    }


@pytest.mark.parametrize(
    "arguments",
    [
        {"limit": 0},
        {"content": ""},
        {"content": "Task", "due": "not-a-date"},
    ],
)
def test_trello_arguments_are_validated(arguments):
    adapter = TrelloAdapter(
        api_key="key", token="token", board_id="board", list_id="list"
    )
    import asyncio

    with pytest.raises(ValueError):
        asyncio.run(adapter.run_capability("productivity.task.list" if "limit" in arguments else "productivity.task.create", arguments))


def test_trello_requires_fixed_scope_configuration():
    with pytest.raises(RuntimeError, match="TRELLO_BOARD_ID"):
        TrelloAdapter(api_key="key", token="token", board_id="bad/id", list_id="list")


def test_trello_configuration_requires_all_server_scoped_values(monkeypatch):
    monkeypatch.setattr(settings, "trello_api_key", "key")
    monkeypatch.setattr(settings, "trello_token", "token")
    monkeypatch.setattr(settings, "trello_board_id", "board")
    monkeypatch.setattr(settings, "trello_list_id", "list")

    assert is_provider_configured(IntegrationProvider.TRELLO) is True
