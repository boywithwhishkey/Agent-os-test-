from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class LinearAdapter(IntegrationAdapter):
    """Read-only Linear GraphQL identity and issue operations."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.linear_api_key or ""
        self._client = client
        if not self.api_key.strip():
            raise RuntimeError("LINEAR_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.LINEAR,
            request,
            reason="Linear mutations are disabled; use the governed issue-list capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._query("query { viewer { id name email } }")
        if capability_id == "tracker.issue.list":
            return await self._query(
                "query { issues(first: 50) { nodes { id identifier title state { name } } } }"
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _query(self, query: str) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                "https://api.linear.app/graphql",
                json={"query": query},
                headers={"Authorization": self.api_key, "Content-Type": "application/json"},
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Linear returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Linear returned HTTP {response.status_code}")
            if not isinstance(body, dict) or body.get("errors"):
                raise RuntimeError("Linear GraphQL returned an error")
            data = body.get("data")
            if not isinstance(data, dict):
                raise TypeError("Linear returned an invalid GraphQL response")
            return data
        except httpx.TimeoutException as exc:
            raise RuntimeError("Linear request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Linear request failed: {type(exc).__name__}") from exc
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
