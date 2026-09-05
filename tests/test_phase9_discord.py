from __future__ import annotations

import httpx
import pytest

from app.integrations.discord import DiscordWebhookAdapter
from app.integrations.factory import build_integration_adapter, is_provider_configured
from app.integrations.models import IntegrationProvider

WEBHOOK = "https://discord.com/api/webhooks/123/secret-token"


@pytest.mark.anyio
async def test_discord_send_posts_only_content() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["json"] = request.read().decode()
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await DiscordWebhookAdapter(webhook_url=WEBHOOK, client=client).run_capability(
            "chat.message.send", {"text": "hello"}
        )
    finally:
        await client.aclose()

    assert result == {"provider": IntegrationProvider.DISCORD.value, "status_code": 204}
    assert seen["url"] == WEBHOOK
    assert seen["json"] == '{"content":"hello"}'


@pytest.mark.anyio
async def test_discord_timeout_is_safe() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="timed out") as exc:
            await DiscordWebhookAdapter(webhook_url=WEBHOOK, client=client).run_capability(
                "chat.message.send", {"content": "hello"}
            )
    finally:
        await client.aclose()
    assert "secret-token" not in str(exc.value)


@pytest.mark.anyio
async def test_discord_http_error_does_not_leak_webhook() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="secret-token should not be surfaced")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 500") as exc:
            await DiscordWebhookAdapter(webhook_url=WEBHOOK, client=client).run_capability(
                "chat.message.send", {"content": "hello"}
            )
    finally:
        await client.aclose()
    assert "secret-token" not in str(exc.value)


def test_discord_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.discord.settings.discord_webhook_url", None)
    with pytest.raises(RuntimeError, match="DISCORD_WEBHOOK_URL"):
        DiscordWebhookAdapter()


def test_discord_factory_and_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.factory.settings.discord_webhook_url", WEBHOOK)
    adapter = build_integration_adapter("discord")
    assert isinstance(adapter, DiscordWebhookAdapter)
    assert is_provider_configured(IntegrationProvider.DISCORD)


@pytest.mark.anyio
async def test_discord_rejects_unsupported_operation() -> None:
    adapter = DiscordWebhookAdapter(webhook_url=WEBHOOK)
    with pytest.raises(Exception, match="has no operation"):
        await adapter.run_capability("chat.message.list", {})
