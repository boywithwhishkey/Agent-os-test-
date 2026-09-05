from __future__ import annotations

import httpx
import pytest

from app.integrations.telegram import TelegramBotAdapter

TOKEN = "123456:telegram-secret-token"


@pytest.mark.anyio
async def test_telegram_identity_and_send_use_fixed_api_methods() -> None:
    calls: list[tuple[str, str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, request.read().decode()))
        if request.url.path.endswith("/getMe"):
            return httpx.Response(200, json={"ok": True, "result": {"id": 1, "username": "bot"}})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 42}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = TelegramBotAdapter(bot_token=TOKEN, default_chat_id="-1001", client=client)
        assert await adapter.run_capability("identity.account.read", {}) == {"id": 1, "username": "bot"}
        result = await adapter.run_capability("chat.message.send", {"text": "hello"})
    finally:
        await client.aclose()

    assert result == {"provider": "telegram", "message_id": 42}
    assert calls == [
        ("GET", "/bot123456:telegram-secret-token/getMe", ""),
        ("POST", "/bot123456:telegram-secret-token/sendMessage", '{"chat_id":"-1001","text":"hello"}'),
    ]


@pytest.mark.anyio
async def test_telegram_provider_errors_never_leak_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"ok": False, "description": "bad token"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 401") as exc:
            await TelegramBotAdapter(bot_token=TOKEN, client=client).run_capability(
                "identity.account.read", {}
            )
    finally:
        await client.aclose()
    assert TOKEN not in str(exc.value)


def test_telegram_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.telegram.settings.telegram_bot_token", None)
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        TelegramBotAdapter()
