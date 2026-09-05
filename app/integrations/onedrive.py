from __future__ import annotations

import time
from typing import Any

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class OneDriveOAuthAdapter(IntegrationAdapter):
    """Read-only Microsoft Graph identity and OneDrive root listing."""

    _BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        *,
        connection_store: OAuthConnectionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.ONEDRIVE,
            request,
            reason="OneDrive file mutations are not enabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("/me", params={"$select": "id,displayName,userPrincipalName"})
        if capability_id == "files.file.list":
            value = arguments.get("max_results", 100)
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 200:
                raise ValueError("max_results must be an integer between 1 and 200")
            return await self._get(
                "/me/drive/root/children",
                params={"$top": str(value), "$select": "id,name,size,file,folder,lastModifiedDateTime"},
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _get(self, path: str, *, params: dict[str, str]) -> dict[str, Any]:
        record = self._connection_store.get("onedrive")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a OneDrive account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["onedrive"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    f"{self._BASE_URL}{path}",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("OneDrive rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"OneDrive returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("OneDrive returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("OneDrive returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("OneDrive request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OneDrive request failed: {type(exc).__name__}") from exc
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
