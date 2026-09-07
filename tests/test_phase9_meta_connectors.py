from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.instagram import InstagramGraphAdapter
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.whatsapp import WhatsAppCloudAdapter

TOKEN = "meta-secret-token"


@pytest.mark.anyio
async def test_whatsapp_identity_and_send_are_fixed_to_configured_phone() -> None:
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.read().decode()))
        if request.method == "GET":
            return httpx.Response(200, json={"id": "phone-1", "verified_name": "Demo"})
        return httpx.Response(200, json={"messages": [{"id": "wamid.1"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = WhatsAppCloudAdapter(
            access_token=TOKEN, phone_number_id="phone-1", api_version="v23.0", client=client
        )
        assert (await adapter.run_capability("identity.account.read", {}))["id"] == "phone-1"
        result = await adapter.run_capability(
            "chat.message.send", {"to": "15551234567", "text": "hello"}
        )
    finally:
        await client.aclose()

    assert result == {"provider": "whatsapp", "status_code": 200, "message_id": "wamid.1"}
    assert seen[0][:2] == ("GET", "/v23.0/phone-1")
    assert seen[1][:2] == ("POST", "/v23.0/phone-1/messages")
    assert "15551234567" in seen[1][2]


@pytest.mark.anyio
async def test_whatsapp_template_send_uses_explicit_bounded_fields() -> None:
    payloads: list[bytes] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payloads.append(request.read())
        return httpx.Response(200, json={"messages": [{"id": "wamid.template.1"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = WhatsAppCloudAdapter(
            access_token=TOKEN, phone_number_id="phone-1", api_version="v23.0", client=client
        )
        result = await adapter.run_capability(
            "chat.template.send",
            {
                "to": "15551234567",
                "template_name": "order_update",
                "language_code": "en_US",
                "body_parameters": ["A-100", "ready"],
            },
        )
    finally:
        await client.aclose()

    assert result == {
        "provider": "whatsapp",
        "status_code": 200,
        "message_id": "wamid.template.1",
        "template_name": "order_update",
    }
    assert json.loads(payloads[0]) == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "15551234567",
        "type": "template",
        "template": {
            "name": "order_update",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "A-100"},
                        {"type": "text", "text": "ready"},
                    ],
                }
            ],
        },
    }


@pytest.mark.anyio
async def test_whatsapp_uses_connected_oauth_token_when_static_token_is_absent() -> None:
    store = OAuthConnectionStore()
    store.record_success("whatsapp", access_token="oauth-meta-token", token_type="bearer", scope="whatsapp_business_messaging")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer oauth-meta-token"
        return httpx.Response(200, json={"id": "phone-1", "verified_name": "Demo"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await WhatsAppCloudAdapter(
            phone_number_id="phone-1", connection_store=store, client=client
        ).run_capability("identity.account.read", {})

    assert result["id"] == "phone-1"


@pytest.mark.anyio
async def test_meta_graph_refreshes_expired_oauth_token_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.oauth.service.settings.meta_oauth_client_id", "meta-client")
    monkeypatch.setattr("app.integrations.oauth.service.settings.meta_oauth_client_secret", "meta-secret")
    store = OAuthConnectionStore()
    store.record_success(
        "whatsapp",
        access_token="expired-meta-token",
        refresh_token="refresh-meta-token",
        token_type="bearer",
        scope="whatsapp_business_messaging",
    )
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/phone-1") and len([p for p in calls if p.endswith("/phone-1")]) == 1:
            return httpx.Response(401, json={"error": {"message": "expired"}})
        if request.url.path.endswith("/oauth/access_token"):
            assert b"grant_type=refresh_token" in request.content
            assert b"refresh_token=refresh-meta-token" in request.content
            return httpx.Response(200, json={"access_token": "fresh-meta-token", "expires_in": 3600})
        assert request.headers["Authorization"] == "Bearer fresh-meta-token"
        return httpx.Response(200, json={"id": "phone-1", "verified_name": "Demo"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await WhatsAppCloudAdapter(
            phone_number_id="phone-1", connection_store=store, client=client
        ).run_capability("identity.account.read", {})

    assert result["id"] == "phone-1"
    assert store.get("whatsapp").access_token == "fresh-meta-token"
    assert calls == ["/v23.0/phone-1", "/v23.0/oauth/access_token", "/v23.0/phone-1"]


@pytest.mark.anyio
async def test_whatsapp_template_send_rejects_unsafe_template_name() -> None:
    adapter = WhatsAppCloudAdapter(access_token=TOKEN, phone_number_id="phone-1")

    with pytest.raises(ValueError, match="alphanumeric template_name"):
        await adapter.run_capability(
            "chat.template.send", {"to": "15551234567", "template_name": "order/update"}
        )


@pytest.mark.anyio
async def test_instagram_identity_and_send_are_fixed_to_configured_account() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"id": "ig-1", "username": "demo"})
        return httpx.Response(200, json={"message_id": "ig-message-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = InstagramGraphAdapter(
            access_token=TOKEN, business_account_id="ig-1", api_version="v23.0", client=client
        )
        assert (await adapter.run_capability("identity.account.read", {}))["username"] == "demo"
        result = await adapter.run_capability(
            "chat.message.send", {"recipient_id": "recipient-1", "text": "hello"}
        )
    finally:
        await client.aclose()

    assert result == {"provider": "instagram", "status_code": 200, "message_id": "ig-message-1"}


@pytest.mark.anyio
async def test_instagram_image_publish_uses_fixed_two_step_graph_flow() -> None:
    seen: list[tuple[str, str, dict[str, str]]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, dict(request.url.params)))
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "container-1"})
        return httpx.Response(200, json={"id": "media-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = InstagramGraphAdapter(
            access_token=TOKEN, business_account_id="ig-1", api_version="v23.0", client=client
        )
        result = await adapter.run_capability(
            "social.post.publish",
            {"image_url": "https://cdn.example.test/photo.jpg", "caption": "hello"},
        )
    finally:
        await client.aclose()

    assert result == {
        "provider": "instagram",
        "container_status_code": 200,
        "publish_status_code": 200,
        "container_id": "container-1",
        "media_id": "media-1",
    }
    assert seen == [
        (
            "POST",
            "/v23.0/ig-1/media",
            {"image_url": "https://cdn.example.test/photo.jpg", "caption": "hello"},
        ),
        ("POST", "/v23.0/ig-1/media_publish", {"creation_id": "container-1"}),
    ]


@pytest.mark.anyio
async def test_instagram_uses_connected_oauth_token_when_static_token_is_absent() -> None:
    store = OAuthConnectionStore()
    store.record_success("instagram", access_token="oauth-meta-token", token_type="bearer", scope="instagram_basic")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer oauth-meta-token"
        return httpx.Response(200, json={"id": "ig-1", "username": "demo"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await InstagramGraphAdapter(
            business_account_id="ig-1", connection_store=store, client=client
        ).run_capability("identity.account.read", {})

    assert result["username"] == "demo"


@pytest.mark.anyio
async def test_instagram_image_publish_rejects_non_https_urls() -> None:
    adapter = InstagramGraphAdapter(access_token=TOKEN, business_account_id="ig-1")

    with pytest.raises(ValueError, match="HTTPS image_url"):
        await adapter.run_capability("social.post.publish", {"image_url": "http://localhost/photo.jpg"})


@pytest.mark.anyio
async def test_meta_errors_do_not_leak_access_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad token"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 401") as exc:
            await WhatsAppCloudAdapter(
                access_token=TOKEN, phone_number_id="phone-1", client=client
            ).run_capability("identity.account.read", {})
    finally:
        await client.aclose()
    assert TOKEN not in str(exc.value)


def test_meta_adapters_require_both_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.whatsapp.settings.meta_access_token", None)
    with pytest.raises(RuntimeError, match="META_ACCESS_TOKEN"):
        WhatsAppCloudAdapter()
    monkeypatch.setattr("app.integrations.instagram.settings.meta_access_token", TOKEN)
    monkeypatch.setattr("app.integrations.instagram.settings.instagram_business_account_id", None)
    with pytest.raises(RuntimeError, match="INSTAGRAM_BUSINESS_ACCOUNT_ID"):
        InstagramGraphAdapter()
