from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class TeamsWebhookAdapter(IntegrationAdapter):
    """Send governed text cards to one operator-configured Teams webhook."""

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.webhook_url = webhook_url or settings.teams_webhook_url or ""
        self._client = client
        if not self.webhook_url.strip():
            raise RuntimeError("TEAMS_WEBHOOK_URL is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.TEAMS,
            request,
            reason="Teams actions must use the governed chat.message.send capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        if capability_id != "chat.message.send":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        content = arguments.get("content", arguments.get("text"))
        if not isinstance(content, str) or not content.strip():
            raise ValueError("chat.message.send requires non-empty text or content")
        if len(content) > 28000:
            raise ValueError("Teams message content must be 28000 characters or fewer")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(self.webhook_url, json={"text": content}, timeout=10.0)
            if not 200 <= response.status_code < 300:
                raise RuntimeError(f"Teams returned HTTP {response.status_code}")
            return {"provider": IntegrationProvider.TEAMS.value, "status_code": response.status_code}
        except httpx.TimeoutException as exc:
            raise RuntimeError("Teams request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Teams request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        """Probe the webhook without sending a message."""
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(self.webhook_url, timeout=10.0)
            latency_ms = (time.perf_counter() - started) * 1000
            return True, latency_ms, None if response.status_code < 500 else f"Teams returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Teams timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: Teams connection failed"
        finally:
            if own_client:
                await client.aclose()
