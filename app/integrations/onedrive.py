from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class OneDriveOAuthAdapter(IntegrationAdapter):
    """Governed Microsoft Graph identity, listing, and file-content operations."""

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
            reason="OneDrive actions must use governed canonical capabilities.",
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
        if capability_id == "files.file.delete":
            path = self._path_argument(arguments, operation="files.file.delete")
            await self._delete_content(path)
            return {"provider": IntegrationProvider.ONEDRIVE.value, "path": path, "deleted": True}
        if capability_id == "files.file.write":
            path, content, mime_type = self._file_payload(arguments)
            return await self._put_content(path, content, mime_type)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _file_payload(arguments: dict[str, Any]) -> tuple[str, bytes, str]:
        path = OneDriveOAuthAdapter._path_argument(arguments, operation="files.file.write")
        mime_type = arguments.get("mime_type", "text/plain")
        if not isinstance(mime_type, str) or not re.fullmatch(r"[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+", mime_type):
            raise ValueError("mime_type must be a valid MIME type")
        content = arguments.get("content")
        if not isinstance(content, str) or not 1 <= len(content.encode("utf-8")) <= 5_000_000:
            raise ValueError("files.file.write requires text content up to 5000000 bytes")
        return path, content.encode("utf-8"), mime_type

    @staticmethod
    def _path_argument(arguments: dict[str, Any], *, operation: str) -> str:
        path = arguments.get("path")
        if (
            not isinstance(path, str)
            or not 2 <= len(path.strip()) <= 400
            or not path.strip().startswith("/")
            or "\x00" in path
            or ".." in path.split("/")
        ):
            raise ValueError(f"{operation} requires a safe absolute OneDrive path")
        return path.strip()

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

    async def _put_content(self, path: str, content: bytes, mime_type: str) -> dict[str, Any]:
        record = self._connection_store.get("onedrive")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a OneDrive account.")
        encoded_path = quote(path, safe="/-_.~")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["onedrive"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.put(
                    f"{self._BASE_URL}/me/drive/root:{encoded_path}:/content",
                    content=content,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": mime_type,
                    },
                    timeout=30.0,
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

    async def _delete_content(self, path: str) -> None:
        record = self._connection_store.get("onedrive")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a OneDrive account.")
        encoded_path = quote(path, safe="/-_.~")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["onedrive"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.delete(
                    f"{self._BASE_URL}/me/drive/root:{encoded_path}:",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("OneDrive rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"OneDrive returned HTTP {response.status_code}")
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
