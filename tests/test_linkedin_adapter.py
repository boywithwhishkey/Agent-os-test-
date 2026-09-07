from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings
from app.integrations.factory import is_provider_configured
from app.integrations.linkedin import LinkedInOAuthAdapter
from app.integrations.models import IntegrationProvider
from app.integrations.oauth.store import OAuthConnectionStore


def _connected_store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        IntegrationProvider.LINKEDIN.value,
        access_token="linkedin-access-token",
        refresh_token="linkedin-refresh-token",
        token_type="Bearer",
        scope="openid w_member_social",
    )
    return store


def test_linkedin_uses_shared_oauth_client_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "linkedin_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "linkedin_oauth_client_secret", "client-secret")
    assert is_provider_configured(IntegrationProvider.LINKEDIN) is True


@pytest.mark.anyio
async def test_linkedin_identity_and_text_post_use_current_api_contract(monkeypatch) -> None:
    monkeypatch.setattr(settings, "linkedin_api_version", "202601")
    seen: list[tuple[str, str, dict[str, str], dict | None]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, dict(request.headers), body))
        if request.url.path == "/v2/userinfo":
            return httpx.Response(200, json={"sub": "member_123", "name": "Nikhil"})
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:123"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = LinkedInOAuthAdapter(connection_store=_connected_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        published = await adapter.run_capability(
            "social.post.publish", {"text": "THYNACT connector update"}
        )
    finally:
        await client.aclose()

    assert identity == {"sub": "member_123", "name": "Nikhil"}
    assert published == {
        "provider": "linkedin",
        "status_code": 201,
        "post_id": "urn:li:share:123",
    }
    assert seen[0][0:2] == ("GET", "/v2/userinfo")
    assert seen[0][2]["authorization"] == "Bearer linkedin-access-token"
    assert seen[2][0:2] == ("POST", "/rest/posts")
    assert seen[2][2]["linkedin-version"] == "202601"
    assert seen[2][2]["x-restli-protocol-version"] == "2.0.0"
    assert seen[2][3] == {
        "author": "urn:li:person:member_123",
        "commentary": {"text": "THYNACT connector update"},
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


@pytest.mark.parametrize(
    "value",
    ["", "x" * 3001],
)
def test_linkedin_post_text_is_bounded(value: str) -> None:
    # Exercise the public validation path without making a network call.
    adapter = LinkedInOAuthAdapter(connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match="3000 characters"):
        import asyncio

        asyncio.run(adapter.run_capability("social.post.publish", {"text": value}))
