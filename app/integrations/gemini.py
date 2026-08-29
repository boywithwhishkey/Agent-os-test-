from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class GeminiAdapter(IntegrationAdapter):
    """Verifies a Gemini API key by listing available models — a free,
    read-only call — rather than generating content."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self._client = client
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.GEMINI,
            request,
            reason="Gemini is used as THYNACT's LLM provider, not a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": self.api_key, "pageSize": 1},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code in (400, 401, 403):
                return False, latency_ms, f"Gemini rejected the API key (HTTP {response.status_code})"
            return False, latency_ms, f"Gemini returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Gemini timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
