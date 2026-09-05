from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class CloudflareAdapter(IntegrationAdapter):
    """Run fixed Cloudflare identity and DNS-record reads."""

    _DOMAIN = re.compile(
        r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}\Z"
    )
    _ZONE_ID = re.compile(r"[A-Za-z0-9]{1,32}\Z")

    def __init__(self, *, api_token: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_token = api_token or settings.cloudflare_api_token
        self._client = client
        if not self.api_token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.CLOUDFLARE,
            request,
            reason="Cloudflare actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/user")
        if capability_id == "cloud.dns.read":
            zone_name = self._zone_name(arguments)
            limit = arguments.get("max_results", 100)
            if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
                raise ValueError("max_results must be an integer between 1 and 500")
            zones = await self._request(
                "GET", "/zones", params={"name": zone_name, "per_page": "5", "page": "1"}
            )
            result = zones.get("result") if isinstance(zones, dict) else None
            if not isinstance(result, list):
                raise RuntimeError("Cloudflare returned an invalid zone list")
            zone = next(
                (
                    item
                    for item in result
                    if isinstance(item, dict) and str(item.get("name", "")).lower() == zone_name
                ),
                None,
            )
            if not isinstance(zone, dict) or not self._ZONE_ID.fullmatch(str(zone.get("id", ""))):
                raise RuntimeError("Cloudflare zone was not found")
            records = await self._request(
                "GET",
                f"/zones/{quote(str(zone['id']), safe='')}/dns_records",
                params={"per_page": str(limit), "page": "1"},
            )
            return {"zone": zone, "records": records}
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @classmethod
    def _zone_name(cls, arguments: dict[str, Any]) -> str:
        value = arguments.get("zone_name")
        if not isinstance(value, str):
            raise TypeError("cloud.dns.read requires a valid zone_name")
        value = value.strip().rstrip(".").lower()
        if not cls._DOMAIN.fullmatch(value):
            raise ValueError("cloud.dns.read requires a valid zone_name")
        return value

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.request(
                method,
                f"https://api.cloudflare.com/client/v4{path}",
                params=params,
                headers={"Authorization": f"Bearer {self.api_token}", "Accept": "application/json"},
                timeout=15.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Cloudflare returned a non-JSON response") from exc
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Cloudflare rejected the API token (HTTP 401)")
                raise RuntimeError(f"Cloudflare returned HTTP {response.status_code}")
            if not isinstance(body, dict) or body.get("success") is not True:
                raise RuntimeError("Cloudflare API returned an unsuccessful response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Cloudflare request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Cloudflare request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            if response.status_code == 200 and body.get("success"):
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "Cloudflare rejected the API token (HTTP 401)"
            return False, latency_ms, f"Cloudflare returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Cloudflare timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
