from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import OAuthExchangeError, request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class SnapchatMarketingAdapter(IntegrationAdapter):
    """Read-only Snapchat Marketing and Public Profile API operations."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        connection_store: OAuthConnectionStore | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.access_token = access_token or settings.connector_credential(
            "SNAPCHAT_ACCESS_TOKEN", settings.snapchat_access_token
        ) or ""
        self._connection_store = connection_store
        self._client = client
        if not self.access_token.strip() and not self._has_oauth_connection():
            raise RuntimeError(
                "SNAPCHAT_ACCESS_TOKEN or a connected Snapchat OAuth account is required"
            )

    def _has_oauth_connection(self) -> bool:
        return bool(self._connection_store and self._connection_store.get("snapchat").access_token)

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SNAPCHAT,
            request,
            reason="Snapchat mutations are not enabled; use the governed identity capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "social.profile.read":
            return await self._get_public_profile(arguments)
        if capability_id not in {"identity.account.read", "ads.account.list"}:
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        body = await self._get_organizations()
        if capability_id == "identity.account.read":
            return body
        organizations = body.get("organizations") or []
        ad_accounts: list[Any] = []
        if isinstance(organizations, list):
            for entry in organizations:
                if not isinstance(entry, dict):
                    continue
                direct_accounts = entry.get("ad_accounts")
                nested_org = entry.get("organization")
                nested_accounts = nested_org.get("ad_accounts") if isinstance(nested_org, dict) else None
                accounts = direct_accounts if isinstance(direct_accounts, list) else nested_accounts
                if isinstance(accounts, list):
                    ad_accounts.extend(accounts)
        return {"provider": IntegrationProvider.SNAPCHAT.value, "ad_accounts": ad_accounts}

    async def _get_public_profile(self, arguments: dict[str, Any]) -> dict[str, Any]:
        profile_id = arguments.get("profile_id")
        if (
            not isinstance(profile_id, str)
            or not 1 <= len(profile_id) <= 128
            or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in profile_id)
        ):
            raise ValueError("social.profile.read requires a valid Snapchat profile_id")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            async def send(token: str) -> httpx.Response:
                return await client.get(
                    f"https://businessapi.snapchat.com/v1/public_profiles/{profile_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )

            if self.access_token.strip():
                response = await send(self.access_token)
            elif self._connection_store is not None:
                response = await request_with_oauth_refresh(
                    OAUTH_PROVIDERS["snapchat"],
                    connection_store=self._connection_store,
                    client=client,
                    send=send,
                )
            else:  # pragma: no cover - constructor prevents this state
                raise OAuthExchangeError("Not authorized yet — connect a Snapchat account")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Snapchat returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Snapchat returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Snapchat returned an invalid response")
            if body.get("request_status") == "ERROR":
                raise RuntimeError("Snapchat rejected the access token")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Snapchat request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Snapchat request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _get_organizations(self) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            async def send(token: str) -> httpx.Response:
                return await client.get(
                    "https://adsapi.snapchat.com/v1/me/organizations",
                    params={"with_ad_accounts": "true"},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )

            if self.access_token.strip():
                response = await send(self.access_token)
            elif self._connection_store is not None:
                response = await request_with_oauth_refresh(
                    OAUTH_PROVIDERS["snapchat"],
                    connection_store=self._connection_store,
                    client=client,
                    send=send,
                )
            else:  # pragma: no cover - constructor prevents this state
                raise OAuthExchangeError("Not authorized yet — connect a Snapchat account")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Snapchat returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Snapchat returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Snapchat returned an invalid response")
            if body.get("request_status") == "ERROR":
                raise RuntimeError("Snapchat rejected the access token")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Snapchat request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Snapchat request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._get_organizations()
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
