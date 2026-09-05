from __future__ import annotations

import base64
import json

import httpx
import pytest

from app.integrations.google import GoogleOAuthAdapter
from app.integrations.models import IntegrationProvider
from app.integrations.oauth.store import OAuthConnectionStore


def _connected_store(provider: IntegrationProvider) -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        provider.value,
        access_token="google-access-token",
        token_type="Bearer",
        scope="read-only",
    )
    return store


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("provider", "capability", "path", "response"),
    [
        (
            IntegrationProvider.GMAIL,
            "identity.account.read",
            "/gmail/v1/users/me/profile",
            {"emailAddress": "person@example.com", "messagesTotal": 3},
        ),
        (
            IntegrationProvider.GOOGLE_CALENDAR,
            "identity.account.read",
            "/calendar/v3/users/me/calendarList",
            {"items": [{"id": "primary"}]},
        ),
        (
            IntegrationProvider.GOOGLE_DRIVE,
            "identity.account.read",
            "/drive/v3/about",
            {"user": {"emailAddress": "person@example.com"}},
        ),
    ],
)
async def test_google_identity_calls_use_bearer_token(
    provider: IntegrationProvider,
    capability: str,
    path: str,
    response: dict,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == path
        assert request.headers["authorization"] == "Bearer google-access-token"
        return httpx.Response(200, json=response)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=provider,
            connection_store=_connected_store(provider),
            client=client,
        )
        result = await adapter.run_capability(capability, {})
    finally:
        await client.aclose()

    assert result == response


@pytest.mark.anyio
async def test_google_read_capabilities_use_provider_endpoints_and_limits() -> None:
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.url.query.decode()))
        return httpx.Response(200, json={"items": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        gmail = GoogleOAuthAdapter(
            provider=IntegrationProvider.GMAIL,
            connection_store=_connected_store(IntegrationProvider.GMAIL),
            client=client,
        )
        calendar = GoogleOAuthAdapter(
            provider=IntegrationProvider.GOOGLE_CALENDAR,
            connection_store=_connected_store(IntegrationProvider.GOOGLE_CALENDAR),
            client=client,
        )
        drive = GoogleOAuthAdapter(
            provider=IntegrationProvider.GOOGLE_DRIVE,
            connection_store=_connected_store(IntegrationProvider.GOOGLE_DRIVE),
            client=client,
        )
        await gmail.run_capability("mail.message.list", {"max_results": 5, "query": "is:unread"})
        await calendar.run_capability("calendar.event.list", {"max_results": 7})
        await drive.run_capability("files.file.list", {"max_results": 9})
    finally:
        await client.aclose()

    assert seen == [
        ("GET", "/gmail/v1/users/me/messages", "maxResults=5&q=is%3Aunread"),
        (
            "GET",
            "/calendar/v3/calendars/primary/events",
            "maxResults=7&singleEvents=true&orderBy=startTime",
        ),
        (
            "GET",
            "/drive/v3/files",
            "pageSize=9&fields=files%28id%2Cname%2CmimeType%2CmodifiedTime%29",
        ),
    ]


@pytest.mark.anyio
async def test_gmail_message_read_uses_fixed_message_endpoint() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"id": "msg_1", "payload": {"headers": []}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GMAIL,
            connection_store=_connected_store(IntegrationProvider.GMAIL),
            client=client,
        )
        result = await adapter.run_capability("mail.message.read", {"message_id": "msg_1"})
    finally:
        await client.aclose()

    assert result == {"id": "msg_1", "payload": {"headers": []}}
    assert seen == {
        "method": "GET",
        "path": "/gmail/v1/users/me/messages/msg_1",
        "query": "format=full",
        "auth": "Bearer google-access-token",
    }


@pytest.mark.parametrize("message_id", ["", "bad/id", "bad\\id", "bad\nheader"])
def test_gmail_message_id_is_validated(message_id: str) -> None:
    with pytest.raises(ValueError, match="message_id"):
        GoogleOAuthAdapter._message_id({"message_id": message_id})


@pytest.mark.anyio
async def test_google_calendar_event_create_uses_fixed_insert_endpoint() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "event_1", "status": "confirmed"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GOOGLE_CALENDAR,
            connection_store=_connected_store(IntegrationProvider.GOOGLE_CALENDAR),
            client=client,
        )
        result = await adapter.run_capability(
            "calendar.event.create",
            {
                "calendar_id": "primary",
                "summary": "Planning",
                "start": "2026-09-05T10:00:00+05:30",
                "end": "2026-09-05T11:00:00+05:30",
                "description": "Weekly planning",
                "timezone": "Asia/Kolkata",
            },
        )
    finally:
        await client.aclose()

    assert result == {"id": "event_1", "status": "confirmed"}
    assert seen == {
        "method": "POST",
        "path": "/calendar/v3/calendars/primary/events",
        "auth": "Bearer google-access-token",
        "body": {
            "summary": "Planning",
            "start": {"dateTime": "2026-09-05T10:00:00+05:30", "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": "2026-09-05T11:00:00+05:30", "timeZone": "Asia/Kolkata"},
            "description": "Weekly planning",
        },
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"summary": "x", "start": "2026-09-05T11:00:00Z", "end": "2026-09-05T10:00:00Z"}, "after start"),
        ({"summary": "x", "start": "2026-09-05T10:00:00", "end": "2026-09-05T11:00:00"}, "timezone offset"),
        ({"summary": "x", "start": "bad", "end": "2026-09-05T11:00:00Z"}, "RFC3339"),
    ],
)
def test_google_calendar_event_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        GoogleOAuthAdapter._event_payload(arguments)


@pytest.mark.anyio
async def test_google_calendar_event_update_and_delete_use_fixed_endpoints() -> None:
    seen: list[tuple[str, str, bytes]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.content))
        if request.method == "PATCH":
            return httpx.Response(200, json={"id": "event_1", "summary": "Updated"})
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GOOGLE_CALENDAR,
            connection_store=_connected_store(IntegrationProvider.GOOGLE_CALENDAR),
            client=client,
        )
        updated = await adapter.run_capability(
            "calendar.event.update",
            {
                "calendar_id": "primary",
                "event_id": "event_1",
                "summary": "Updated",
                "start": "2026-09-05T10:00:00+05:30",
                "end": "2026-09-05T11:00:00+05:30",
            },
        )
        deleted = await adapter.run_capability(
            "calendar.event.delete", {"calendar_id": "primary", "event_id": "event_1"}
        )
    finally:
        await client.aclose()

    assert updated["summary"] == "Updated"
    assert deleted == {"provider": "google_calendar", "event_id": "event_1", "deleted": True}
    assert seen[0][0:2] == ("PATCH", "/calendar/v3/calendars/primary/events/event_1")
    assert seen[1][0:2] == ("DELETE", "/calendar/v3/calendars/primary/events/event_1")


def test_google_calendar_event_identifier_is_validated() -> None:
    with pytest.raises(ValueError, match="event_id"):
        GoogleOAuthAdapter._event_identifier({"event_id": "bad/id"})


@pytest.mark.anyio
async def test_gmail_draft_create_posts_gmail_mime_payload() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        payload = json.loads(request.content)
        raw = payload["message"]["raw"]
        decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode()
        seen["mime"] = decoded
        return httpx.Response(200, json={"id": "draft_1", "message": {"id": "msg_1"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GMAIL,
            connection_store=_connected_store(IntegrationProvider.GMAIL),
            client=client,
        )
        result = await adapter.run_capability(
            "mail.draft.create",
            {
                "to": ["person@example.com"],
                "cc": "copy@example.com",
                "subject": "Planning",
                "body": "Let's meet tomorrow.",
            },
        )
    finally:
        await client.aclose()

    assert result["id"] == "draft_1"
    assert seen["method"] == "POST"
    assert seen["path"] == "/gmail/v1/users/me/drafts"
    assert seen["auth"] == "Bearer google-access-token"
    assert "To: person@example.com" in seen["mime"]
    assert "Cc: copy@example.com" in seen["mime"]
    assert "Subject: Planning" in seen["mime"]
    assert "Let's meet tomorrow." in seen["mime"]


@pytest.mark.anyio
async def test_gmail_message_send_posts_gmail_mime_payload() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        payload = json.loads(request.content)
        raw = payload["raw"]
        seen["mime"] = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode()
        return httpx.Response(200, json={"id": "msg_1", "threadId": "thread_1", "labelIds": ["SENT"]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GMAIL,
            connection_store=_connected_store(IntegrationProvider.GMAIL),
            client=client,
        )
        result = await adapter.run_capability(
            "mail.message.send",
            {
                "to": "person@example.com",
                "subject": "Planning",
                "body": "Let's meet tomorrow.",
            },
        )
    finally:
        await client.aclose()

    assert result == {"id": "msg_1", "threadId": "thread_1", "labelIds": ["SENT"]}
    assert seen["method"] == "POST"
    assert seen["path"] == "/gmail/v1/users/me/messages/send"
    assert seen["auth"] == "Bearer google-access-token"
    assert "To: person@example.com" in seen["mime"]
    assert "Subject: Planning" in seen["mime"]
    assert "Let's meet tomorrow." in seen["mime"]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"to": "bad", "subject": "x", "body": "body"}, "recipients"),
        ({"to": "a@example.com", "subject": "", "body": "body"}, "subject"),
        ({"to": "a@example.com", "subject": "x", "body": "bad\nheader"}, "line breaks"),
    ],
)
def test_gmail_draft_arguments_are_validated(arguments: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        GoogleOAuthAdapter._draft_raw(arguments)


@pytest.mark.anyio
async def test_google_drive_file_write_uses_multipart_upload() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        seen["auth"] = request.headers["authorization"]
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = request.content
        return httpx.Response(200, json={"id": "file_1", "name": "notes.txt", "size": "12"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GOOGLE_DRIVE,
            connection_store=_connected_store(IntegrationProvider.GOOGLE_DRIVE),
            client=client,
        )
        result = await adapter.run_capability(
            "files.file.write",
            {
                "name": "notes.txt",
                "mime_type": "text/plain",
                "content": "hello drive",
                "parent_id": "folder_1",
            },
        )
    finally:
        await client.aclose()

    assert result["id"] == "file_1"
    assert seen["method"] == "POST"
    assert seen["path"] == "/upload/drive/v3/files"
    assert seen["query"] == "uploadType=multipart&fields=id%2Cname%2CmimeType%2Csize"
    assert seen["auth"] == "Bearer google-access-token"
    assert "multipart/related; boundary=thynact-drive-boundary" == seen["content_type"]
    assert b'"name":"notes.txt","mimeType":"text/plain","parents":["folder_1"]' in seen["body"]
    assert b"hello drive" in seen["body"]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"name": "../bad", "content": "x"}, "file name"),
        ({"name": "x.txt", "mime_type": "bad", "content": "x"}, "MIME"),
        ({"name": "x.txt", "content": ""}, "text content"),
    ],
)
def test_google_drive_file_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        GoogleOAuthAdapter._file_payload(arguments)


@pytest.mark.anyio
async def test_google_missing_connection_is_explicit_and_secret_safe() -> None:
    store = OAuthConnectionStore()
    adapter = GoogleOAuthAdapter(
        provider=IntegrationProvider.GMAIL,
        connection_store=store,
    )

    connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is not None
    assert error == "Not authorized yet — use Authorize to connect a Gmail account."


@pytest.mark.anyio
async def test_google_unauthorized_response_never_exposes_token() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_token"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleOAuthAdapter(
            provider=IntegrationProvider.GOOGLE_DRIVE,
            connection_store=_connected_store(IntegrationProvider.GOOGLE_DRIVE),
            client=client,
        )
        connected, _, error = await adapter.test_connection()
    finally:
        await client.aclose()

    assert connected is False
    assert error == "Google Drive rejected the stored token (HTTP 401) — authorize again"
    assert "google-access-token" not in error


def test_google_limit_is_bounded() -> None:
    adapter = GoogleOAuthAdapter(
        provider=IntegrationProvider.GMAIL,
        connection_store=OAuthConnectionStore(),
    )
    with pytest.raises(ValueError, match="between 1 and 100"):
        adapter._limit_params({"max_results": 101})
