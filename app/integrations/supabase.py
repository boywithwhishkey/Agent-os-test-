from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


class SupabaseAdapter(IntegrationAdapter):
    """Read-only Supabase REST access to one server-configured table."""

    def __init__(
        self,
        *,
        url: str | None = None,
        anon_key: str | None = None,
        read_table: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.url = self._normalize_url(url or settings.supabase_url or "")
        self.anon_key = anon_key or settings.supabase_anon_key or ""
        self.read_table = (read_table or settings.supabase_read_table or "").strip()
        self._client = client
        if not self.url:
            raise RuntimeError("SUPABASE_URL must be an HTTPS URL")
        if not self.anon_key:
            raise RuntimeError("SUPABASE_ANON_KEY is required")
        if not _TABLE_RE.fullmatch(self.read_table):
            raise RuntimeError("SUPABASE_READ_TABLE must be a simple table name")

    @staticmethod
    def _normalize_url(value: str) -> str:
        candidate = value.strip().rstrip("/")
        parts = urlsplit(candidate)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.path not in {"", "/"}:
            return ""
        return candidate

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SUPABASE,
            request,
            reason="Supabase writes/auth/storage mutations are not enabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id != "data.record.read":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        value = arguments.get("limit", 100)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 1000:
            raise ValueError("limit must be an integer between 1 and 1000")
        return await self._get({"select": "*", "limit": str(value)})

    async def _get(self, params: dict[str, str]) -> list[dict[str, Any]]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                f"{self.url}/rest/v1/{self.read_table}",
                params=params,
                headers={"apikey": self.anon_key, "Authorization": f"Bearer {self.anon_key}"},
                timeout=10.0,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Supabase returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Supabase returned a non-JSON response") from exc
            if not isinstance(body, list):
                raise TypeError("Supabase returned an invalid table response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Supabase request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Supabase request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("data.record.read", {"limit": 1})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
