from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

_API_ROOT = "https://api.pinterest.com/v5"
_USER_URL = f"{_API_ROOT}/user_account"
_PINS_URL = f"{_API_ROOT}/pins"
_BOARD_ID_RE = re.compile(r"^\d{1,18}$")


class PinterestOAuthAdapter(IntegrationAdapter):
    """Governed Pinterest account reads and image Pin publishing."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.PINTEREST,
            request,
            reason="Pinterest actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get_user()
        if capability_id == "social.post.publish":
            return await self._create_pin(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _get_user(self) -> dict[str, Any]:
        response = await self._request("GET", _USER_URL, timeout=10.0)
        return self._json_body(response, "Pinterest user account")

    async def _create_pin(self, arguments: dict[str, Any]) -> dict[str, Any]:
        board_id = arguments.get("board_id")
        if not isinstance(board_id, str) or not _BOARD_ID_RE.fullmatch(board_id):
            raise ValueError("social.post.publish requires a numeric Pinterest board_id")
        image_url = arguments.get("image_url")
        if not isinstance(image_url, str) or not self._is_public_https_url(image_url):
            raise ValueError("social.post.publish requires an HTTPS image_url")
        if len(image_url) > 2_048:
            raise ValueError("Pinterest image_url must be 2048 characters or fewer")
        title = arguments.get("title", "")
        description = arguments.get("description", arguments.get("caption", ""))
        link = arguments.get("link")
        if not isinstance(title, str) or len(title) > 100:
            raise ValueError("Pinterest title must be 100 characters or fewer")
        if not isinstance(description, str) or len(description) > 500:
            raise ValueError("Pinterest description must be 500 characters or fewer")
        if link is not None and (not isinstance(link, str) or not self._is_public_https_url(link)):
            raise ValueError("Pinterest link must be an HTTPS URL")

        payload: dict[str, Any] = {
            "board_id": board_id,
            "media_source": {"source_type": "image_url", "url": image_url},
        }
        if title.strip():
            payload["title"] = title.strip()
        if description.strip():
            payload["description"] = description.strip()
        if link is not None:
            payload["link"] = link.strip()

        response = await self._request("POST", _PINS_URL, json=payload, timeout=15.0)
        body = self._json_body(response, "Pinterest Create Pin")
        pin_id = body.get("id")
        if not isinstance(pin_id, str) or not pin_id:
            raise RuntimeError("Pinterest did not return a Pin id")
        return {
            "provider": IntegrationProvider.PINTEREST.value,
            "status_code": response.status_code,
            "pin_id": pin_id,
            "board_id": board_id,
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        timeout: float,
    ) -> httpx.Response:
        record = self._connection_store.get(IntegrationProvider.PINTEREST.value)
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Pinterest account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()

        async def send(token: str) -> httpx.Response:
            return await client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json,
                timeout=timeout,
            )

        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[IntegrationProvider.PINTEREST.value],
                connection_store=self._connection_store,
                client=client,
                send=send,
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Pinterest rejected the stored token (HTTP 401) — authorize again")
                detail = ""
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        detail = str(body.get("message") or body.get("code") or "")
                except ValueError:
                    pass
                raise RuntimeError(f"Pinterest returned HTTP {response.status_code}{': ' + detail if detail else ''}")
            return response
        except httpx.TimeoutException as exc:
            raise RuntimeError("Pinterest request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Pinterest request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _json_body(response: httpx.Response, name: str) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(f"{name} returned a non-JSON response") from exc
        if not isinstance(body, dict):
            raise TypeError(f"{name} returned an invalid response")
        return body

    @staticmethod
    def _is_public_https_url(value: str) -> bool:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme.lower() == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and parsed.hostname.lower() not in {"localhost", "127.0.0.1", "::1"}
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._get_user()
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
