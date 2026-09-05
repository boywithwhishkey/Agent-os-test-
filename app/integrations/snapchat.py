from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class SnapchatMarketingAdapter(IntegrationAdapter):
    """Read-only Snapchat Marketing API organization discovery."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.access_token = access_token or settings.snapchat_access_token or ""
        self._client = client
        if not self.access_token.strip():
            raise RuntimeError("SNAPCHAT_ACCESS_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SNAPCHAT,
            request,
            reason="Snapchat mutations are not enabled; use the governed identity capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id != "identity.account.read":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        return await self._get_organizations()

    async def _get_organizations(self) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                "https://adsapi.snapchat.com/v1/me/organizations",
                params={"with_ad_accounts": "true"},
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Snapchat returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Snapchat returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Snapchat returned an invalid response")
            if body.get("request_status") == "ERROR":
                raise RuntimeError("Snapchat rejected the access token")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Snapchat request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Snapchat request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._get_organizations()
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
