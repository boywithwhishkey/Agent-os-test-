from __future__ import annotations

import time

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class MakeWebhookAdapter(IntegrationAdapter):
    """Triggers a single configured Make (Integromat) scenario webhook.

    Unlike n8n (a self-hosted base URL + per-workflow path), a Make webhook
    URL is a single opaque per-scenario endpoint — there's no common host to
    address multiple scenarios from one base URL. This adapter therefore
    points at exactly one webhook; `request.workflow` is carried through as
    a label in the payload rather than a URL path segment, so the operator
    can still tell which logical trigger fired on the Make side.
    """

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        auth_header: str | None = None,
        auth_value: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.webhook_url = webhook_url or settings.make_webhook_url or ""
        self.auth_header = auth_header or settings.make_webhook_auth_header
        self.auth_value = auth_value or settings.make_webhook_auth_value
        self._client = client

        if not self.webhook_url.strip():
            raise RuntimeError("MAKE_WEBHOOK_URL is required")

    def _headers(self, request: IntegrationRequest) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if request.correlation_id:
            headers["X-Agent-OS-Correlation-ID"] = request.correlation_id
        if self.auth_header and self.auth_value:
            headers[self.auth_header] = self.auth_value
        return headers

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                self.webhook_url,
                json={"_workflow": request.workflow, **request.payload},
                headers=self._headers(request),
                timeout=request.timeout_seconds,
            )
            try:
                data = response.json()
            except ValueError:
                data = response.text

            if 200 <= response.status_code < 300:
                return IntegrationResult(
                    provider=IntegrationProvider.MAKE,
                    workflow=request.workflow,
                    success=True,
                    status_code=response.status_code,
                    data=data,
                    correlation_id=request.correlation_id,
                )
            return IntegrationResult(
                provider=IntegrationProvider.MAKE,
                workflow=request.workflow,
                success=False,
                status_code=response.status_code,
                data=data,
                error=f"Make returned HTTP {response.status_code}",
                correlation_id=request.correlation_id,
            )
        except httpx.TimeoutException:
            return IntegrationResult(
                provider=IntegrationProvider.MAKE,
                workflow=request.workflow,
                success=False,
                error="Make request timed out",
                correlation_id=request.correlation_id,
            )
        except httpx.HTTPError as exc:
            return IntegrationResult(
                provider=IntegrationProvider.MAKE,
                workflow=request.workflow,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                correlation_id=request.correlation_id,
            )
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        """Probe reachability of the configured webhook. Make's webhook
        endpoints reject GET (405) but that still confirms the host and
        path are reachable — same "any HTTP status counts as reachable"
        approach as the n8n adapter, since Make exposes no dedicated health
        route either."""
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            await client.get(self.webhook_url, timeout=10.0)
            latency_ms = (time.perf_counter() - started) * 1000
            return True, latency_ms, None
        except httpx.TimeoutException:
            return False, None, "Connection to Make timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
