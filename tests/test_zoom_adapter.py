from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.zoom import ZoomOAuthAdapter


def _store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success("zoom", access_token="zoom-token", token_type="Bearer", scope="meeting")
    return store


@pytest.mark.anyio
async def test_zoom_identity_and_meeting_list_use_fixed_routes():
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.url.query.decode()))
        if request.url.path.endswith("/users/me") and not request.url.path.endswith("/meetings"):
            return httpx.Response(200, json={"id": "user-1", "email": "person@example.com"})
        return httpx.Response(200, json={"meetings": [{"id": "meeting-1"}], "total_records": 1})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = ZoomOAuthAdapter(connection_store=_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        meetings = await adapter.run_capability("meeting.session.list", {"limit": 2})

    assert identity == {"id": "user-1", "email": "person@example.com"}
    assert meetings == {"meetings": [{"id": "meeting-1"}], "total_records": 1}
    assert seen == [
        ("GET", "/v2/users/me", ""),
        ("GET", "/v2/users/me/meetings", "page_size=2&type=scheduled"),
    ]


@pytest.mark.anyio
async def test_zoom_meeting_create_uses_fixed_scheduled_type_and_bounded_payload():
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": "meeting-new", "join_url": "https://zoom.example/join"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await ZoomOAuthAdapter(connection_store=_store(), client=client).run_capability(
            "meeting.session.create",
            {
                "topic": "Connector review",
                "start_time": "2026-09-08T10:00:00+05:30",
                "duration": 45,
                "timezone": "Asia/Kolkata",
                "agenda": "Review connector status",
            },
        )

    assert result == {"id": "meeting-new", "join_url": "https://zoom.example/join"}
    assert seen == {
        "method": "POST",
        "path": "/v2/users/me/meetings",
        "body": {
            "topic": "Connector review",
            "type": 2,
            "start_time": "2026-09-08T10:00:00+05:30",
            "duration": 45,
            "timezone": "Asia/Kolkata",
            "agenda": "Review connector status",
        },
    }


@pytest.mark.parametrize(
    "arguments",
    [
        {"limit": 0},
        {"topic": "x", "start_time": "bad"},
        {"topic": "x", "start_time": "2026-09-08T10:00:00", "duration": 30},
    ],
)
def test_zoom_arguments_are_validated(arguments):
    adapter = ZoomOAuthAdapter(connection_store=_store())
    import asyncio

    capability = "meeting.session.list" if "limit" in arguments else "meeting.session.create"
    with pytest.raises(ValueError):
        asyncio.run(adapter.run_capability(capability, arguments))


@pytest.mark.anyio
async def test_zoom_missing_connection_is_honest():
    connected, latency_ms, error = await ZoomOAuthAdapter(
        connection_store=OAuthConnectionStore()
    ).test_connection()
    assert connected is False
    assert latency_ms is None
    assert "Zoom" in (error or "")
