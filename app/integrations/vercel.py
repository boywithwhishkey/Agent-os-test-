from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class VercelAdapter(IntegrationAdapter):
    """Read-only Vercel identity and project status operations."""

    def __init__(
        self,
        *,
        api_token: str | None = None,
        team_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_token = api_token or settings.vercel_api_token or ""
        self.team_id = team_id or settings.vercel_team_id
        self._client = client
        if not self.api_token.strip():
            raise RuntimeError("VERCEL_API_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.VERCEL,
            request,
            reason="Vercel deploy mutations are disabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("/v2/user")
        if capability_id == "cloud.service.read":
            params = {"limit": "100"}
            if self.team_id:
                params["teamId"] = self.team_id
            return await self._get("/v9/projects", params=params)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                f"https://api.vercel.com{path}",
                params=params,
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Vercel returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Vercel returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Vercel returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Vercel request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Vercel request failed: {type(exc).__name__}") from exc
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
