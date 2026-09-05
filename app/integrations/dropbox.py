from __future__ import annotations

import base64
import json
import time
from typing import Any

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class DropboxOAuthAdapter(IntegrationAdapter):
    """Governed Dropbox account, metadata, and file-content operations."""

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
            reason="Dropbox actions must use governed canonical capabilities.",
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
        if capability_id == "files.file.read":
            path = self._path_argument(arguments, operation="files.file.read")
            return await self._download(path)
        if capability_id == "files.file.delete":
            path = self._path_argument(arguments, operation="files.file.delete")
            body = await self._post(
                "https://api.dropboxapi.com/2/files/delete_v2",
                {"path": path},
            )
            return {
                "provider": IntegrationProvider.DROPBOX.value,
                "path": path,
                "deleted": True,
                "metadata": body.get("metadata"),
            }
        if capability_id == "files.file.write":
            path, content, mode = self._file_payload(arguments)
            return await self._upload(path, content, mode)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _file_payload(arguments: dict[str, Any]) -> tuple[str, bytes, str]:
        path = DropboxOAuthAdapter._path_argument(arguments, operation="files.file.write")
        content = arguments.get("content")
        if not isinstance(content, str) or not 1 <= len(content.encode("utf-8")) <= 5_000_000:
            raise ValueError("files.file.write requires text content up to 5000000 bytes")
        mode = arguments.get("mode", "add")
        if mode not in {"add", "overwrite"}:
            raise ValueError("mode must be add or overwrite")
        return path, content.encode("utf-8"), mode

    @staticmethod
    def _path_argument(arguments: dict[str, Any], *, operation: str) -> str:
        path = arguments.get("path")
        if (
            not isinstance(path, str)
            or not 2 <= len(path.strip()) <= 1024
            or not path.strip().startswith("/")
            or "\x00" in path
            or ".." in path.split("/")
        ):
            raise ValueError(f"{operation} requires a safe absolute Dropbox path")
        return path.strip()

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self._connection_store.get("dropbox")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Dropbox account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["dropbox"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
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

    async def _upload(self, path: str, content: bytes, mode: str) -> dict[str, Any]:
        record = self._connection_store.get("dropbox")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Dropbox account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["dropbox"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    "https://content.dropboxapi.com/2/files/upload",
                    content=content,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Dropbox-API-Arg": json.dumps(
                            {"path": path, "mode": mode, "autorename": False, "mute": False},
                            separators=(",", ":"),
                        ),
                        "Content-Type": "application/octet-stream",
                    },
                    timeout=30.0,
                ),
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

    async def _download(self, path: str) -> dict[str, Any]:
        record = self._connection_store.get("dropbox")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Dropbox account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["dropbox"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    "https://content.dropboxapi.com/2/files/download",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Dropbox-API-Arg": json.dumps({"path": path}, separators=(",", ":")),
                        "Content-Type": "application/octet-stream",
                    },
                    timeout=30.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Dropbox rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Dropbox returned HTTP {response.status_code}")
            content_length = response.headers.get("content-length")
            if content_length and content_length.isdigit() and int(content_length) > 5_000_000:
                raise RuntimeError("Dropbox file exceeds the 5000000 byte read limit")
            content = response.content
            if len(content) > 5_000_000:
                raise RuntimeError("Dropbox file exceeds the 5000000 byte read limit")
            metadata: dict[str, Any] | None = None
            raw_metadata = response.headers.get("dropbox-api-result")
            if raw_metadata:
                try:
                    parsed = json.loads(raw_metadata)
                    if isinstance(parsed, dict):
                        metadata = parsed
                except ValueError:
                    metadata = None
            return {
                "provider": IntegrationProvider.DROPBOX.value,
                "path": path,
                "content_base64": base64.b64encode(content).decode("ascii"),
                "content_type": response.headers.get("content-type"),
                "size": len(content),
                "metadata": metadata,
            }
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
