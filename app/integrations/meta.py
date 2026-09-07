from __future__ import annotations

from typing import Any

import httpx

from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class MetaGraphClient:
    """Small, secret-safe client for fixed Meta Graph API resources."""

    def __init__(
        self,
        *,
        access_token: str,
        api_version: str,
        client: httpx.AsyncClient | None = None,
        oauth_provider: str | None = None,
        connection_store: OAuthConnectionStore | None = None,
    ) -> None:
        self._access_token = access_token
        self._base_url = f"https://graph.facebook.com/{api_version.strip('/') }"
        self._client = client
        self._oauth_provider = oauth_provider
        self._connection_store = connection_store

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            async def send(token: str) -> httpx.Response:
                return await client.request(
                    method,
                    f"{self._base_url}/{path.strip('/')}",
                    params=params,
                    json=json,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )

            if self._oauth_provider and self._connection_store:
                response = await request_with_oauth_refresh(
                    OAUTH_PROVIDERS[self._oauth_provider],
                    connection_store=self._connection_store,
                    client=client,
                    send=send,
                )
            else:
                response = await send(self._access_token)
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Meta Graph returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Meta Graph returned an invalid response")
            if response.status_code >= 400 or body.get("error"):
                raise RuntimeError(f"Meta Graph returned HTTP {response.status_code}")
            return body, response.status_code
        except httpx.TimeoutException as exc:
            raise RuntimeError("Meta Graph request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Meta Graph request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()
