from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class VercelAdapter(IntegrationAdapter):
    """Run fixed Vercel reads and a configured, approval-gated deploy hook."""

    _HOOK_PATH = re.compile(r"/v1/integrations/deploy/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+\Z")

    def __init__(
        self,
        *,
        api_token: str | None = None,
        team_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_token = api_token or settings.vercel_api_token or ""
        self.team_id = team_id or settings.vercel_team_id
        self.deploy_hook_url = settings.vercel_deploy_hook_url
        self._client = client
        if not self.api_token.strip():
            raise RuntimeError("VERCEL_API_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.VERCEL,
            request,
            reason="Vercel actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("/v2/user")
        if capability_id == "cloud.service.read":
            params = {"limit": "100"}
            if self.team_id:
                params["teamId"] = self.team_id
            return await self._get("/v9/projects", params=params)
        if capability_id == "cloud.deploy.trigger":
            return await self._trigger_deploy_hook(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _trigger_deploy_hook(self, arguments: dict[str, Any]) -> dict[str, Any]:
        url = self._validated_hook_url()
        build_cache = arguments.get("build_cache")
        if build_cache is not None:
            if not isinstance(build_cache, bool):
                raise TypeError("build_cache must be a boolean")
            url = f"{url}?buildCache={'true' if build_cache else 'false'}"
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(url, timeout=30.0)
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Vercel returned a non-JSON deploy response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Vercel deploy hook returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Vercel returned an invalid deploy response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Vercel deploy hook timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Vercel deploy hook failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    def _validated_hook_url(self) -> str:
        value = self.deploy_hook_url
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError("VERCEL_DEPLOY_HOOK_URL is required for cloud.deploy.trigger")
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.vercel.com"
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not self._HOOK_PATH.fullmatch(parsed.path)
        ):
            raise RuntimeError("VERCEL_DEPLOY_HOOK_URL must be a valid Vercel deploy hook URL")
        return value.strip()

    async def _get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                f"https://api.vercel.com{path}",
                params=params,
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Vercel returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Vercel returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Vercel returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Vercel request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Vercel request failed: {type(exc).__name__}") from exc
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
