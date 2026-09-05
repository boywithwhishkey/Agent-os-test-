from __future__ import annotations

import httpx
import pytest

from app.integrations.instagram import InstagramGraphAdapter
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
