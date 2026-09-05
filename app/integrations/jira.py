from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class JiraOAuthAdapter(IntegrationAdapter):
    """Read-only Jira Cloud REST operations using an OAuth 2.0 (3LO) token."""

    def __init__(
        self,
        *,
        cloud_id: str | None = None,
        connection_store: OAuthConnectionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.cloud_id = (cloud_id or settings.jira_cloud_id or "").strip()
        self._connection_store = connection_store
        self._client = client
        if not self.cloud_id:
            raise RuntimeError("JIRA_CLOUD_ID is required")

    @property
    def _base_url(self) -> str:
        return f"https://api.atlassian.com/ex/jira/{self.cloud_id}/rest/api/3"

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.JIRA,
            request,
            reason="Jira mutations are not enabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/myself")
        if capability_id == "tracker.issue.list":
            return await self._request(
                "POST",
                "/search/jql",
                json={
                    "jql": self._jql(arguments),
                    "maxResults": self._max_results(arguments),
                    "fields": ["summary", "status", "issuetype", "project"],
                },
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _jql(arguments: dict[str, Any]) -> str:
        value = arguments.get("jql", "ORDER BY updated DESC")
        if not isinstance(value, str) or not value.strip() or len(value) > 2000:
            raise ValueError("jql must be a non-empty string of at most 2000 characters")
        return value.strip()

    @staticmethod
    def _max_results(arguments: dict[str, Any]) -> int:
        value = arguments.get("max_results", 25)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("max_results must be an integer between 1 and 100")
        return value

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = self._connection_store.get("jira")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Jira account.")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["jira"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.request(
                    method,
                    f"{self._base_url}{path}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    json=json,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Jira rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Jira returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Jira returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Jira returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Jira request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Jira request failed: {type(exc).__name__}") from exc
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
