from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class RenderAdapter(IntegrationAdapter):
    """Verifies a Render API key by listing the owners visible to it — a
    cheap, read-only identity check."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.render_api_key
        self._client = client
        if not self.api_key:
            raise RuntimeError("RENDER_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.RENDER,
            request,
            reason="Render deploy triggers are not yet wired to a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.render.com/v1/owners",
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "Render rejected the API key (HTTP 401)"
            return False, latency_ms, f"Render returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Render timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
