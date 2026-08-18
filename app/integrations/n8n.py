from __future__ import annotations

import os
from urllib.parse import urljoin

import httpx

from app.integrations.base import IntegrationAdapter
from app.integrations.models import (
    IntegrationProvider,
    IntegrationRequest,
    IntegrationResult,
)


class N8NWebhookAdapter(IntegrationAdapter):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        webhook_prefix: str | None = None,
        auth_header: str | None = None,
        auth_value: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("N8N_BASE_URL", "")).rstrip("/") + "/"
        self.webhook_prefix = (
            webhook_prefix or os.getenv("N8N_WEBHOOK_PREFIX", "webhook")
        ).strip("/")
        self.auth_header = auth_header or os.getenv("N8N_WEBHOOK_AUTH_HEADER")
        self.auth_value = auth_value or os.getenv("N8N_WEBHOOK_AUTH_VALUE")
        self._client = client

        if not self.base_url.strip("/"):
            raise RuntimeError("N8N_BASE_URL is required")

    def _url(self, workflow: str) -> str:
        safe_name = workflow.strip("/")
        return urljoin(self.base_url, f"{self.webhook_prefix}/{safe_name}")

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
                self._url(request.workflow),
                json=request.payload,
                headers=self._headers(request),
                timeout=request.timeout_seconds,
            )

            try:
                data = response.json()
            except ValueError:
                data = response.text

            if 200 <= response.status_code < 300:
                return IntegrationResult(
                    provider=IntegrationProvider.N8N,
                    workflow=request.workflow,
                    success=True,
                    status_code=response.status_code,
                    data=data,
                    correlation_id=request.correlation_id,
                )

            return IntegrationResult(
                provider=IntegrationProvider.N8N,
                workflow=request.workflow,
                success=False,
                status_code=response.status_code,
                data=data,
                error=f"n8n returned HTTP {response.status_code}",
                correlation_id=request.correlation_id,
            )

        except httpx.TimeoutException:
            return IntegrationResult(
                provider=IntegrationProvider.N8N,
                workflow=request.workflow,
                success=False,
                error="n8n request timed out",
                correlation_id=request.correlation_id,
            )
        except httpx.HTTPError as exc:
            return IntegrationResult(
                provider=IntegrationProvider.N8N,
                workflow=request.workflow,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                correlation_id=request.correlation_id,
            )
        finally:
            if own_client:
                await client.aclose()
