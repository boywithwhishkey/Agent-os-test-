from __future__ import annotations

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
