from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class SalesforceOAuthAdapter(IntegrationAdapter):
    """Read-only Salesforce REST queries against one configured org."""

    def __init__(
        self,
        *,
        instance_url: str | None = None,
        api_version: str | None = None,
        connection_store: OAuthConnectionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.instance_url = self._normalize_url(instance_url or settings.salesforce_instance_url or "")
        self.api_version = api_version or settings.salesforce_api_version
        self._connection_store = connection_store
        self._client = client
        if not self.instance_url:
            raise RuntimeError("SALESFORCE_INSTANCE_URL is required")

    @staticmethod
    def _normalize_url(value: str) -> str:
        candidate = value.strip().rstrip("/")
        parts = urlsplit(candidate)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.path not in {"", "/"}:
            return ""
        return candidate

    @property
    def _endpoint(self) -> str:
        return f"{self.instance_url}/services/data/{self.api_version}/query"

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SALESFORCE,
            request,
            reason="Salesforce CRM mutations are not enabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._query("SELECT Id, Name FROM Organization LIMIT 1")
        if capability_id == "crm.contact.list":
            return await self._query(
                "SELECT Id, FirstName, LastName, Email FROM Contact "
                f"LIMIT {self._limit(arguments)}"
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 100)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 200:
            raise ValueError("limit must be an integer between 1 and 200")
        return value

    async def _query(self, soql: str) -> dict[str, Any]:
        record = self._connection_store.get("salesforce")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Salesforce account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["salesforce"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    self._endpoint,
                    params={"q": soql},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Salesforce rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Salesforce returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Salesforce returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Salesforce returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Salesforce request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Salesforce request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
