from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class TelegramBotAdapter(IntegrationAdapter):
    """Governed text messaging through one server-configured Telegram bot."""

    def __init__(
        self,
        *,
        bot_token: str | None = None,
        default_chat_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.bot_token = bot_token or settings.telegram_bot_token or ""
        self.default_chat_id = default_chat_id or settings.telegram_default_chat_id
        self._client = client
        if not self.bot_token.strip():
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    @property
    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}"

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.TELEGRAM,
            request,
            reason="Telegram actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get_me()
        if capability_id != "chat.message.send":
            raise CapabilityNotWired(
                f"{type(self).__name__} has no operation for {capability_id}"
            )

        chat_id = arguments.get("chat_id", self.default_chat_id)
        if not isinstance(chat_id, (str, int)) or isinstance(chat_id, bool) or not str(chat_id).strip():
            raise ValueError("chat.message.send requires a chat_id or TELEGRAM_DEFAULT_CHAT_ID")
        text = arguments.get("text", arguments.get("content"))
        if not isinstance(text, str) or not text.strip():
            raise ValueError("chat.message.send requires non-empty text or content")
        if len(text) > 4096:
            raise ValueError("Telegram message text must be 4096 characters or fewer")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                f"{self._base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10.0,
            )
            body = self._json_body(response)
            if response.status_code >= 400 or body.get("ok") is not True:
                raise RuntimeError(f"Telegram rejected the message (HTTP {response.status_code})")
            return {"provider": IntegrationProvider.TELEGRAM.value, "message_id": body.get("result", {}).get("message_id")}
        except httpx.TimeoutException as exc:
            raise RuntimeError("Telegram request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Telegram request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _get_me(self) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(f"{self._base_url}/getMe", timeout=10.0)
            body = self._json_body(response)
            if response.status_code >= 400 or body.get("ok") is not True:
                raise RuntimeError(f"Telegram rejected the bot token (HTTP {response.status_code})")
            return body.get("result", {})
        except httpx.TimeoutException as exc:
            raise RuntimeError("Telegram request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Telegram request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _json_body(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._get_me()
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
