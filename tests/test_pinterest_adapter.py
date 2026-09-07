from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings
from app.integrations.factory import is_provider_configured
from app.integrations.models import IntegrationProvider
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.pinterest import PinterestOAuthAdapter


def _connected_store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        IntegrationProvider.PINTEREST.value,
        access_token="pinterest-access-token",
        refresh_token="pinterest-refresh-token",
        token_type="Bearer",
        scope="user_accounts:read pins:write",
    )
    return store


def test_pinterest_uses_shared_oauth_client_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "pinterest_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "pinterest_oauth_client_secret", "client-secret")
    assert is_provider_configured(IntegrationProvider.PINTEREST) is True


@pytest.mark.anyio
async def test_pinterest_identity_and_image_pin_use_v5_contract() -> None:
    seen: list[tuple[str, str, dict[str, str], dict | None]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, dict(request.headers), body))
        if request.url.path == "/v5/user_account":
            return httpx.Response(200, json={"username": "thynact", "account_type": "BUSINESS"})
        return httpx.Response(201, json={"id": "123456789", "board_id": "987654321"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = PinterestOAuthAdapter(connection_store=_connected_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        published = await adapter.run_capability(
            "social.post.publish",
            {
                "board_id": "987654321",
                "image_url": "https://cdn.example.com/photo.jpg",
                "title": "THYNACT",
                "description": "A governed Pinterest Pin",
                "link": "https://app.thynact.com",
            },
        )
    finally:
        await client.aclose()

    assert identity["username"] == "thynact"
    assert published == {
        "provider": "pinterest",
        "status_code": 201,
        "pin_id": "123456789",
        "board_id": "987654321",
    }
    assert seen[0][0:2] == ("GET", "/v5/user_account")
    assert seen[0][2]["authorization"] == "Bearer pinterest-access-token"
    assert seen[1][0:2] == ("POST", "/v5/pins")
    assert seen[1][3] == {
        "board_id": "987654321",
        "media_source": {
            "source_type": "image_url",
            "url": "https://cdn.example.com/photo.jpg",
        },
        "title": "THYNACT",
        "description": "A governed Pinterest Pin",
        "link": "https://app.thynact.com",
    }


@pytest.mark.parametrize(
    "arguments, message",
    [
        ({"board_id": "abc", "image_url": "https://cdn.example.com/photo.jpg"}, "board_id"),
        ({"board_id": "1", "image_url": "http://cdn.example.com/photo.jpg"}, "HTTPS"),
        ({"board_id": "1", "image_url": "https://localhost/photo.jpg"}, "HTTPS"),
        ({"board_id": "1", "image_url": "https://cdn.example.com/photo.jpg", "title": "x" * 101}, "100"),
    ],
)
def test_pinterest_pin_arguments_are_bounded(arguments: dict, message: str) -> None:
    adapter = PinterestOAuthAdapter(connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match=message):
        import asyncio

        asyncio.run(adapter.run_capability("social.post.publish", arguments))
