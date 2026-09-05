from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class DiscordWebhookAdapter(IntegrationAdapter):
    """Send governed messages to one operator-configured Discord webhook.

    The webhook URL is server configuration, never request data. This adapter
    intentionally exposes one canonical capability and does not accept an
    arbitrary Discord endpoint from a workflow.
    """

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.webhook_url = webhook_url or settings.discord_webhook_url or ""
        self._client = client
        if not self.webhook_url.strip():
            raise RuntimeError("DISCORD_WEBHOOK_URL is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.DISCORD,
            request,
            reason="Discord actions must use the governed chat.message.send capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        if capability_id != "chat.message.send":
            raise CapabilityNotWired(
                f"{type(self).__name__} has no operation for {capability_id}"
            )

        content = arguments.get("content", arguments.get("text"))
        if not isinstance(content, str) or not content.strip():
            raise ValueError("chat.message.send requires non-empty text or content")
        if len(content) > 2000:
            raise ValueError("Discord message content must be 2000 characters or fewer")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                self.webhook_url,
                json={"content": content},
                timeout=10.0,
            )
            if not 200 <= response.status_code < 300:
                raise RuntimeError(f"Discord returned HTTP {response.status_code}")
            return {"provider": IntegrationProvider.DISCORD.value, "status_code": response.status_code}
        except httpx.TimeoutException as exc:
            raise RuntimeError("Discord request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Discord request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        """Read webhook metadata without posting a message."""
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(self.webhook_url, timeout=10.0)
            latency_ms = (time.perf_counter() - started) * 1000
            if 200 <= response.status_code < 300:
                return True, latency_ms, None
            return False, latency_ms, f"Discord returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Discord timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: Discord connection failed"
        finally:
            if own_client:
                await client.aclose()
