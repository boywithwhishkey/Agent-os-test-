from __future__ import annotations

import httpx
import pytest

from app.core.config import settings
from app.integrations.factory import is_provider_configured
from app.integrations.models import IntegrationProvider
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.reddit import RedditOAuthAdapter


def _connected_store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        IntegrationProvider.REDDIT.value,
        access_token="reddit-access-token",
        refresh_token="reddit-refresh-token",
        token_type="bearer",
        scope="identity read submit",
    )
    return store


def test_reddit_uses_shared_oauth_client_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "reddit_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "reddit_oauth_client_secret", "client-secret")
    assert is_provider_configured(IntegrationProvider.REDDIT) is True


@pytest.mark.anyio
async def test_reddit_identity_and_text_post_use_oauth_contract(monkeypatch) -> None:
    monkeypatch.setattr(settings, "reddit_user_agent", "THYNACT/test by operator")
    seen: list[tuple[str, str, dict[str, str], dict[str, str] | None]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        # The test only needs to inspect the encoded fields below; parse the
        # real body as a normal form when the endpoint is called.
        if request.url.path == "/api/v1/me":
            seen.append((request.method, request.url.path, dict(request.headers), None))
            return httpx.Response(200, json={"name": "thynact", "id": "abc"})
        from urllib.parse import parse_qsl

        parsed = dict(parse_qsl(request.content.decode()))
        seen.append((request.method, request.url.path, dict(request.headers), parsed))
        return httpx.Response(
            200,
            json={"json": {"data": {"name": "t3_abc123", "url": "https://reddit.com/r/test"}}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = RedditOAuthAdapter(connection_store=_connected_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        published = await adapter.run_capability(
            "social.post.publish",
            {"subreddit": "thynact", "title": "Connector update", "text": "Hello Reddit"},
        )
    finally:
        await client.aclose()

    assert identity["name"] == "thynact"
    assert published == {
        "provider": "reddit",
        "status_code": 200,
        "post_id": "t3_abc123",
        "subreddit": "thynact",
    }
    assert seen[0][0:2] == ("GET", "/api/v1/me")
    assert seen[0][2]["authorization"] == "Bearer reddit-access-token"
    assert seen[0][2]["user-agent"] == "THYNACT/test by operator"
    assert seen[1][0:2] == ("POST", "/api/submit")
    assert seen[1][3] == {
        "sr": "thynact",
        "title": "Connector update",
        "kind": "self",
        "resubmit": "false",
        "sendreplies": "true",
        "spoiler": "false",
        "nsfw": "false",
        "text": "Hello Reddit",
    }


@pytest.mark.parametrize(
    "arguments, message",
    [
        ({"subreddit": "bad-name", "title": "Title", "text": "Body"}, "subreddit"),
        ({"subreddit": "thynact", "title": "Title"}, "requires text or url"),
        (
            {"subreddit": "thynact", "title": "Title", "text": "Body", "url": "https://example.com"},
            "text or url",
        ),
        ({"subreddit": "thynact", "title": "Title", "url": "http://example.com"}, "HTTPS"),
    ],
)
def test_reddit_post_arguments_are_bounded(arguments: dict, message: str) -> None:
    adapter = RedditOAuthAdapter(connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match=message):
        import asyncio

        asyncio.run(adapter.run_capability("social.post.publish", arguments))
