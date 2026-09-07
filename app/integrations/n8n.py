from __future__ import annotations

import json
import re
import time
from urllib.parse import urljoin

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter
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
        self.base_url = (
            base_url
            or settings.connector_credential("N8N_BASE_URL", settings.n8n_base_url)
            or ""
        ).rstrip("/") + "/"
        self.webhook_prefix = (
            webhook_prefix or settings.n8n_webhook_prefix
        ).strip("/")
        self.auth_header = auth_header or settings.connector_credential(
            "N8N_WEBHOOK_AUTH_HEADER", settings.n8n_auth_header
        )
        self.auth_value = auth_value or settings.connector_credential(
            "N8N_WEBHOOK_AUTH_VALUE", settings.n8n_auth_value
        )
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

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        if capability_id != "automation.workflow.trigger":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        result = await self.execute(self._canonical_request(arguments))
        if not result.success:
            raise RuntimeError(result.error or "n8n workflow trigger failed")
        return {
            "provider": IntegrationProvider.N8N.value,
            "status_code": result.status_code,
            "data": result.data,
        }

    @staticmethod
    def _canonical_request(arguments: dict) -> IntegrationRequest:
        workflow = arguments.get("workflow")
        if (
            not isinstance(workflow, str)
            or not 1 <= len(workflow.strip()) <= 200
            or workflow.startswith("/")
            or ".." in workflow.split("/")
            or not re.fullmatch(r"[A-Za-z0-9._/-]+", workflow.strip())
        ):
            raise ValueError("automation.workflow.trigger requires a safe workflow path")
        payload = arguments.get("payload", {})
        if not isinstance(payload, dict) or len(payload) > 50:
            raise ValueError("automation.workflow.trigger payload must be an object with at most 50 fields")
        try:
            if len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")) > 100_000:
                raise ValueError("automation.workflow.trigger payload must be 100000 UTF-8 bytes or fewer")
        except (TypeError, ValueError) as exc:
            raise ValueError("automation.workflow.trigger payload must be JSON serializable") from exc
        timeout = arguments.get("timeout_seconds", 30.0)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 1 <= timeout <= 120:
            raise ValueError("timeout_seconds must be between 1 and 120")
        return IntegrationRequest(workflow=workflow.strip(), payload=payload, timeout_seconds=float(timeout))

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        """Probe reachability of the configured n8n host.

        n8n exposes no generic health route on arbitrary instances, so this
        checks that the base host responds at all (any HTTP status counts as
        reachable) rather than pretending a specific workflow succeeded.
        """
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            await client.get(self.base_url, timeout=10.0)
            latency_ms = (time.perf_counter() - started) * 1000
            return True, latency_ms, None
        except httpx.TimeoutException:
            return False, None, "Connection to n8n timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
