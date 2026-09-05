from __future__ import annotations

from typing import Any

import httpx


class MetaGraphClient:
    """Small, secret-safe client for fixed Meta Graph API resources."""

    def __init__(
        self,
        *,
        access_token: str,
        api_version: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._access_token = access_token
        self._base_url = f"https://graph.facebook.com/{api_version.strip('/') }"
        self._client = client

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
            response = await client.request(
                method,
                f"{self._base_url}/{path.strip('/')}",
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {self._access_token}"},
                timeout=10.0,
            )
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
