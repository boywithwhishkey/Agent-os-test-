from __future__ import annotations

import time
from typing import Any

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.store import OAuthConnectionStore


class DropboxOAuthAdapter(IntegrationAdapter):
    """Read-only Dropbox account and root-file metadata operations."""

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
            IntegrationProvider.DROPBOX,
            request,
            reason="Dropbox file mutations are not enabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._post("https://api.dropboxapi.com/2/users/get_current_account", {})
        if capability_id == "files.file.list":
            value = arguments.get("max_results", 100)
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 1000:
                raise ValueError("max_results must be an integer between 1 and 1000")
            return await self._post(
                "https://api.dropboxapi.com/2/files/list_folder",
                {"path": "", "recursive": False, "include_deleted": False, "limit": value},
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self._connection_store.get("dropbox")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Dropbox account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {record.access_token}"},
                timeout=10.0,
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Dropbox rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Dropbox returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Dropbox returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Dropbox returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Dropbox request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Dropbox request failed: {type(exc).__name__}") from exc
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
