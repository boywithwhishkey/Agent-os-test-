from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
_POSTS_URL = "https://api.linkedin.com/rest/posts"
_MEMBER_SUB_RE = re.compile(r"^[A-Za-z0-9_-]{1,160}$")


class LinkedInOAuthAdapter(IntegrationAdapter):
    """Governed LinkedIn member identity and text publishing.

    The adapter intentionally exposes only the member-level text post path.
    Organization publishing, media uploads, comments, and analytics require
    separate LinkedIn products/permissions and are not implied by a member
    OAuth connection.
    """

    def __init__(
        self,
        *,
        connection_store: OAuthConnectionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._connection_store = connection_store
        self._client = client
        self._api_version = settings.linkedin_api_version.strip()
        if not re.fullmatch(r"20\d{4}", self._api_version):
            raise RuntimeError("LINKEDIN_API_VERSION must be a YYYYMM value")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.LINKEDIN,
            request,
            reason="LinkedIn actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._userinfo()
        if capability_id == "social.post.publish":
            return await self._publish_text(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _userinfo(self) -> dict[str, Any]:
        response = await self._request(
            "GET",
            _USERINFO_URL,
            timeout=10.0,
        )
        return self._json_body(response, "LinkedIn userinfo")

    async def _publish_text(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = arguments.get("text", arguments.get("commentary"))
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 3_000:
            raise ValueError("social.post.publish requires text between 1 and 3000 characters")
        identity = await self._userinfo()
        subject = identity.get("sub")
        if not isinstance(subject, str) or not _MEMBER_SUB_RE.fullmatch(subject):
            raise RuntimeError("LinkedIn userinfo did not return a usable member id")
        response = await self._request(
            "POST",
            _POSTS_URL,
            json={
                "author": f"urn:li:person:{subject}",
                "commentary": {"text": text.strip()},
                "visibility": "PUBLIC",
                "distribution": {"feedDistribution": "MAIN_FEED"},
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            },
            timeout=15.0,
            post=True,
        )
        body = self._json_body(response, "LinkedIn Posts API", allow_empty=True)
        return {
            "provider": IntegrationProvider.LINKEDIN.value,
            "status_code": response.status_code,
            "post_id": response.headers.get("x-restli-id") or body.get("id"),
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        timeout: float,
        post: bool = False,
    ) -> httpx.Response:
        record = self._connection_store.get(IntegrationProvider.LINKEDIN.value)
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a LinkedIn account.")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        headers = {"Authorization": "Bearer {token}"}
        if post:
            headers.update(
                {
                    "Content-Type": "application/json",
                    "LinkedIn-Version": self._api_version,
                    "X-Restli-Protocol-Version": "2.0.0",
                }
            )

        async def send(token: str) -> httpx.Response:
            request_headers = {key: value.replace("{token}", token) for key, value in headers.items()}
            return await client.request(
                method,
                url,
                headers=request_headers,
                json=json,
                timeout=timeout,
            )

        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[IntegrationProvider.LINKEDIN.value],
                connection_store=self._connection_store,
                client=client,
                send=send,
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("LinkedIn rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"LinkedIn returned HTTP {response.status_code}")
            return response
        except httpx.TimeoutException as exc:
            raise RuntimeError("LinkedIn request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"LinkedIn request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _json_body(
        response: httpx.Response, name: str, *, allow_empty: bool = False
    ) -> dict[str, Any]:
        if not response.content and allow_empty:
            return {}
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(f"{name} returned a non-JSON response") from exc
        if not isinstance(body, dict):
            raise TypeError(f"{name} returned an invalid response")
        return body

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._userinfo()
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
