from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

_OAUTH_ROOT = "https://oauth.reddit.com"
_ME_URL = f"{_OAUTH_ROOT}/api/v1/me"
_SUBMIT_URL = f"{_OAUTH_ROOT}/api/submit"
_SUBREDDIT_RE = re.compile(r"^[A-Za-z0-9_]{2,21}$")


class RedditOAuthAdapter(IntegrationAdapter):
    """Governed Reddit identity and approval-gated post submission."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.REDDIT,
            request,
            reason="Reddit actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get_me()
        if capability_id == "social.post.publish":
            return await self._submit_post(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _get_me(self) -> dict[str, Any]:
        response = await self._request("GET", _ME_URL, timeout=10.0)
        return self._json_body(response, "Reddit account")

    async def _submit_post(self, arguments: dict[str, Any]) -> dict[str, Any]:
        subreddit = arguments.get("subreddit")
        if not isinstance(subreddit, str) or not _SUBREDDIT_RE.fullmatch(subreddit.strip()):
            raise ValueError("social.post.publish requires a valid subreddit name")
        title = arguments.get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 300:
            raise ValueError("Reddit post title must be between 1 and 300 characters")

        text = arguments.get("text", arguments.get("body"))
        url = arguments.get("url")
        if text is not None and url is not None:
            raise ValueError("Reddit post must provide text or url, not both")
        if text is None and url is None:
            raise ValueError("Reddit post requires text or url")
        if text is not None and (not isinstance(text, str) or not 1 <= len(text) <= 10_000):
            raise ValueError("Reddit self-post text must be between 1 and 10000 characters")
        if url is not None and (not isinstance(url, str) or not self._is_public_https_url(url)):
            raise ValueError("Reddit link posts require an HTTPS URL")
        for field in ("spoiler", "nsfw", "send_replies"):
            if field in arguments and not isinstance(arguments[field], bool):
                raise TypeError(f"{field} must be a boolean")

        form: dict[str, str] = {
            "sr": subreddit.strip(),
            "title": title.strip(),
            "kind": "self" if text is not None else "link",
            "resubmit": "false",
            "sendreplies": str(arguments.get("send_replies", True)).lower(),
            "spoiler": str(arguments.get("spoiler", False)).lower(),
            "nsfw": str(arguments.get("nsfw", False)).lower(),
        }
        if text is not None:
            form["text"] = text
        else:
            form["url"] = str(url).strip()

        response = await self._request("POST", _SUBMIT_URL, data=form, timeout=15.0)
        body = self._json_body(response, "Reddit submit")
        wrapper = body.get("json")
        data = wrapper.get("data") if isinstance(wrapper, dict) else None
        if not isinstance(data, dict):
            raise TypeError("Reddit submit did not return a post payload")
        post_id = data.get("name") or data.get("id")
        if not isinstance(post_id, str) or not post_id:
            raise RuntimeError("Reddit submit did not return a post id")
        return {
            "provider": IntegrationProvider.REDDIT.value,
            "status_code": response.status_code,
            "post_id": post_id,
            "subreddit": subreddit.strip(),
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        record = self._connection_store.get(IntegrationProvider.REDDIT.value)
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Reddit account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        headers = {
            "Authorization": "Bearer {token}",
            "User-Agent": settings.reddit_user_agent.strip(),
            "Accept": "application/json",
        }

        async def send(token: str) -> httpx.Response:
            request_headers = {key: value.replace("{token}", token) for key, value in headers.items()}
            return await client.request(
                method,
                url,
                headers=request_headers,
                data=data,
                timeout=timeout,
            )

        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[IntegrationProvider.REDDIT.value],
                connection_store=self._connection_store,
                client=client,
                send=send,
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Reddit rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Reddit returned HTTP {response.status_code}")
            return response
        except httpx.TimeoutException as exc:
            raise RuntimeError("Reddit request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Reddit request failed: {type(exc).__name__}") from exc
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
            await self._get_me()
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
