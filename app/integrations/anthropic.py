from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

ANTHROPIC_API_VERSION = "2023-06-01"


class AnthropicAdapter(IntegrationAdapter):
    """Verifies an Anthropic API key with a harmless, free read call (listing
    models) rather than an actual message. THYNACT does not currently run
    Claude as an LLM provider itself, so execute() is unsupported here."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self._client = client
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.ANTHROPIC,
            request,
            reason="Anthropic is a model provider, not a triggered workflow.",
        )

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        """`ai.model.list` — the model ids this key can actually reach."""
        if capability_id != "ai.model.list":
            return await super().run_capability(capability_id, arguments)
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_API_VERSION,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
            return {"models": sorted(m["id"] for m in payload.get("data", []) if "id" in m)}
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": self.api_key, "anthropic-version": ANTHROPIC_API_VERSION},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "Anthropic rejected the API key (HTTP 401)"
            return False, latency_ms, f"Anthropic returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Anthropic timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
