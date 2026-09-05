from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class RenderAdapter(IntegrationAdapter):
    """Run fixed Render service reads and approval-gated deploy triggers."""

    _SERVICE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
    _COMMIT_ID = re.compile(r"[0-9A-Fa-f]{7,64}\Z")

    def __init__(
        self,
        *,
        api_key: str | None = None,
        service_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or settings.render_api_key
        self.service_id = service_id or settings.render_service_id
        self._client = client
        if not self.api_key:
            raise RuntimeError("RENDER_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.RENDER,
            request,
            reason="Render actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/v1/owners")
        if capability_id == "cloud.service.read":
            limit = arguments.get("max_results", 25)
            if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
                raise ValueError("max_results must be an integer between 1 and 100")
            return await self._request("GET", "/v1/services", params={"limit": str(limit)})
        if capability_id == "cloud.deploy.trigger":
            service_id, payload = self._deploy_payload(arguments, default_service_id=self.service_id)
            return await self._request(
                "POST",
                f"/v1/services/{quote(service_id, safe='-_')}/deploys",
                json=payload,
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @classmethod
    def _deploy_payload(
        cls,
        arguments: dict[str, Any],
        *,
        default_service_id: str | None = None,
    ) -> tuple[str, dict[str, str]]:
        service_id = arguments.get("service_id") or default_service_id
        if not isinstance(service_id, str) or not cls._SERVICE_ID.fullmatch(service_id.strip()):
            raise ValueError("cloud.deploy.trigger requires a valid Render service_id")
        deploy_mode = arguments.get("deploy_mode", "build_and_deploy")
        if deploy_mode not in {"build_and_deploy", "deploy_only"}:
            raise ValueError("deploy_mode must be build_and_deploy or deploy_only")
        clear_cache = arguments.get("clear_cache", False)
        if not isinstance(clear_cache, bool):
            raise TypeError("clear_cache must be a boolean")
        payload: dict[str, str] = {
            "clearCache": "clear" if clear_cache else "do_not_clear",
            "deployMode": deploy_mode,
        }
        commit_id = arguments.get("commit_id")
        if commit_id is not None:
            if not isinstance(commit_id, str) or not cls._COMMIT_ID.fullmatch(commit_id.strip()):
                raise ValueError("commit_id must be a 7-64 character hexadecimal SHA")
            payload["commitId"] = commit_id.strip()
        return service_id.strip(), payload

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> object:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.request(
                method,
                f"https://api.render.com{path}",
                params=params,
                json=json,
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
                timeout=30.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Render returned a non-JSON response") from exc
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Render rejected the API key (HTTP 401)")
                raise RuntimeError(f"Render returned HTTP {response.status_code}")
            if not isinstance(body, (dict, list)):
                raise TypeError("Render returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Render request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Render request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.render.com/v1/owners",
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "Render rejected the API key (HTTP 401)"
            return False, latency_ms, f"Render returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Render timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
