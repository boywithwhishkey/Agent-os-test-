from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.outlook import OutlookOAuthAdapter


def _store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success("outlook", access_token="outlook-token", token_type="Bearer", scope="mail")
    return store


@pytest.mark.anyio
async def test_outlook_identity_and_message_list_use_fixed_graph_routes():
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.headers["authorization"]))
        if request.url.path == "/v1.0/me":
            return httpx.Response(200, json={"id": "user-1"})
        return httpx.Response(200, json={"value": [{"id": "message-1"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = OutlookOAuthAdapter(connection_store=_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        messages = await adapter.run_capability("mail.message.list", {"limit": 2})

    assert identity == {"id": "user-1"}
    assert messages == {"value": [{"id": "message-1"}]}
    assert seen == [
        ("GET", "/v1.0/me", "Bearer outlook-token"),
        ("GET", "/v1.0/me/messages", "Bearer outlook-token"),
    ]


@pytest.mark.anyio
async def test_outlook_send_mail_and_create_event_use_approval_capabilities():
    seen: list[tuple[str, str, dict]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, json.loads(request.content)))
        if request.url.path.endswith("sendMail"):
            return httpx.Response(202)
        return httpx.Response(201, json={"id": "event-1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = OutlookOAuthAdapter(connection_store=_store(), client=client)
        sent = await adapter.run_capability(
            "mail.message.send",
            {"subject": "Hello", "body": "World", "to": "person@example.com"},
        )
        event = await adapter.run_capability(
            "calendar.event.create",
            {
                "subject": "Demo",
                "start": "2026-09-07T10:00:00Z",
                "end": "2026-09-07T11:00:00Z",
                "timezone": "UTC",
            },
        )

    assert sent == {"status_code": 202}
    assert event == {"id": "event-1"}
    assert seen[0][1] == "/v1.0/me/sendMail"
    assert seen[1][1] == "/v1.0/me/calendar/events"


def test_outlook_validates_message_and_event_arguments():
    with pytest.raises(ValueError, match="recipients"):
        import asyncio

        asyncio.run(
            OutlookOAuthAdapter._send_message(
                OutlookOAuthAdapter.__new__(OutlookOAuthAdapter),
                {"subject": "Hi", "body": "Body", "to": "not-an-email"},
            )
        )
    with pytest.raises(ValueError, match="ISO-8601"):
        import asyncio

        asyncio.run(
            OutlookOAuthAdapter._create_event(
                OutlookOAuthAdapter.__new__(OutlookOAuthAdapter),
                {"subject": "Demo", "start": "bad", "end": "bad"},
            )
        )


@pytest.mark.anyio
async def test_outlook_test_connection_reports_missing_connection():
    connected, latency_ms, error = await OutlookOAuthAdapter(
        connection_store=OAuthConnectionStore()
    ).test_connection()
    assert connected is False
    assert latency_ms is None
    assert "Microsoft Outlook" in (error or "")
