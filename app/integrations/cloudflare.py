from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class CloudflareAdapter(IntegrationAdapter):
    """Verifies a Cloudflare API token via Cloudflare's dedicated token
    verification endpoint — a read-only, zero-side-effect call designed
    exactly for this purpose."""

    def __init__(self, *, api_token: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_token = api_token or settings.cloudflare_api_token
        self._client = client
        if not self.api_token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.CLOUDFLARE,
            request,
            reason="Cloudflare actions (DNS, Pages deploys) are not yet wired to a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            if response.status_code == 200 and body.get("success"):
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "Cloudflare rejected the API token (HTTP 401)"
            return False, latency_ms, f"Cloudflare returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Cloudflare timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
