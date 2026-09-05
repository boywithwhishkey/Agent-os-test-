from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class HubSpotOAuthAdapter(IntegrationAdapter):
    """Governed HubSpot account and CRM contact operations."""

    _BASE_URL = "https://api.hubapi.com"

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
            IntegrationProvider.HUBSPOT,
            request,
            reason="HubSpot actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("/account-info/v3/details")
        if capability_id == "crm.contact.list":
            return await self._get(
                "/crm/v3/objects/contacts",
                params={"limit": str(self._limit(arguments)), "properties": "email,firstname,lastname"},
            )
        if capability_id == "crm.contact.update":
            identifier, id_property, properties = self._contact_update_payload(arguments)
            return await self._patch(
                f"/crm/v3/objects/contacts/{quote(identifier, safe='')}",
                properties,
                params={"idProperty": id_property} if id_property else None,
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 100)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _contact_update_payload(arguments: dict[str, Any]) -> tuple[str, str | None, dict[str, str]]:
        contact_id = arguments.get("contact_id")
        email = arguments.get("email")
        if (contact_id is None) == (email is None):
            raise ValueError("crm.contact.update requires exactly one of contact_id or email")
        if contact_id is not None:
            if not isinstance(contact_id, str) or not 1 <= len(contact_id.strip()) <= 64 or "/" in contact_id:
                raise ValueError("contact_id must be a safe HubSpot contact identifier")
            identifier, id_property = contact_id.strip(), None
        else:
            if (
                not isinstance(email, str)
                or not 3 <= len(email.strip()) <= 320
                or "@" not in email
                or any(char in email for char in "\r\n/")
            ):
                raise ValueError("email must be a valid HubSpot contact email")
            identifier, id_property = email.strip(), "email"

        properties = arguments.get("properties")
        if not isinstance(properties, dict) or not 1 <= len(properties) <= 20:
            raise ValueError("crm.contact.update requires 1-20 properties")
        validated: dict[str, str] = {}
        for name, value in properties.items():
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,99}", name):
                raise ValueError("HubSpot property names must be safe identifiers")
            if not isinstance(value, str) or len(value) > 1000:
                raise ValueError("HubSpot property values must be strings of 1000 characters or fewer")
            validated[name] = value
        return identifier, id_property, validated

    async def _get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        record = self._connection_store.get("hubspot")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a HubSpot account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["hubspot"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    f"{self._BASE_URL}{path}",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("HubSpot rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"HubSpot returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("HubSpot returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("HubSpot returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("HubSpot request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"HubSpot request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _patch(
        self,
        path: str,
        properties: dict[str, str],
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        record = self._connection_store.get("hubspot")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a HubSpot account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["hubspot"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.patch(
                    f"{self._BASE_URL}{path}",
                    params=params,
                    json={"properties": properties},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("HubSpot rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"HubSpot returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("HubSpot returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("HubSpot returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("HubSpot request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"HubSpot request failed: {type(exc).__name__}") from exc
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
