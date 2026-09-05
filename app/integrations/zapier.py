from __future__ import annotations

import time
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class ZapierWebhookAdapter(IntegrationAdapter):
    """Trigger one fixed Zapier webhook without accepting caller URLs."""

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        auth_header: str | None = None,
        auth_value: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.webhook_url = self._normalize_url(webhook_url or settings.zapier_webhook_url or "")
        self.auth_header = auth_header or settings.zapier_webhook_auth_header
        self.auth_value = auth_value or settings.zapier_webhook_auth_value
        self._client = client
        if not self.webhook_url:
            raise RuntimeError("ZAPIER_WEBHOOK_URL must be an HTTPS URL")

    @staticmethod
    def _normalize_url(value: str) -> str:
        candidate = value.strip()
        parts = urlsplit(candidate)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            return ""
        return candidate

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
            return IntegrationResult(
                provider=IntegrationProvider.ZAPIER,
                workflow=request.workflow,
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                data=data,
                error=None if 200 <= response.status_code < 300 else f"Zapier returned HTTP {response.status_code}",
                correlation_id=request.correlation_id,
            )
        except httpx.TimeoutException:
            return IntegrationResult(
                provider=IntegrationProvider.ZAPIER,
                workflow=request.workflow,
                success=False,
                error="Zapier request timed out",
                correlation_id=request.correlation_id,
            )
        except httpx.HTTPError as exc:
            return IntegrationResult(
                provider=IntegrationProvider.ZAPIER,
                workflow=request.workflow,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                correlation_id=request.correlation_id,
            )
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            await client.get(self.webhook_url, timeout=10.0)
            return True, (time.perf_counter() - started) * 1000, None
        except httpx.TimeoutException:
            return False, None, "Connection to Zapier timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
