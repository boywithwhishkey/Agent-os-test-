from __future__ import annotations

import httpx
import pytest

from app.integrations.teams import TeamsWebhookAdapter

WEBHOOK = "https://example.webhook.office.com/webhookb2/secret"


@pytest.mark.anyio
async def test_teams_send_uses_fixed_webhook_and_text_payload() -> None:
    seen: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"success": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await TeamsWebhookAdapter(webhook_url=WEBHOOK, client=client).run_capability(
            "chat.message.send", {"text": "hello"}
        )
    finally:
        await client.aclose()
    assert result == {"provider": "teams", "status_code": 200}
    assert seen == {"url": WEBHOOK, "body": '{"text":"hello"}'}


@pytest.mark.anyio
async def test_teams_error_does_not_leak_webhook() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="secret")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 500") as exc:
            await TeamsWebhookAdapter(webhook_url=WEBHOOK, client=client).run_capability(
                "chat.message.send", {"content": "hello"}
            )
    finally:
        await client.aclose()
    assert "secret" not in str(exc.value)


def test_teams_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.teams.settings.teams_webhook_url", None)
    with pytest.raises(RuntimeError, match="TEAMS_WEBHOOK_URL"):
        TeamsWebhookAdapter()
