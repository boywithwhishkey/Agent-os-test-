from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

_BASE_URL = "https://people.googleapis.com/v1"
_IDENTITY_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_PERSON_FIELDS = "names,emailAddresses,phoneNumbers,organizations,metadata"
_EMAIL_RE = re.compile(r"^[^@\s]{1,128}@[^@\s]{1,255}\.[^@\s]{2,63}$")


class GoogleContactsOAuthAdapter(IntegrationAdapter):
    """Governed Google Contacts reads and approval-gated contact creation."""

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
            IntegrationProvider.GOOGLE_CONTACTS,
            request,
            reason="Google Contacts actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", _IDENTITY_URL)
        if capability_id == "crm.contact.list":
            params = {
                "personFields": _PERSON_FIELDS,
                "pageSize": str(self._limit(arguments)),
                "sortOrder": "LAST_MODIFIED_ASCENDING",
            }
            page_token = arguments.get("page_token")
            if page_token is not None:
                params["pageToken"] = self._page_token(page_token)
            return await self._request(
                "GET", f"{_BASE_URL}/people/me/connections", params=params
            )
        if capability_id == "crm.contact.create":
            return await self._request(
                "POST",
                f"{_BASE_URL}/people:createContact",
                params={"personFields": _PERSON_FIELDS},
                json=self._contact_payload(arguments),
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 50)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("crm.contact.list limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _page_token(value: object) -> str:
        if (
            not isinstance(value, str)
            or not 1 <= len(value.strip()) <= 2048
            or any(ord(char) < 0x20 for char in value)
        ):
            raise ValueError("page_token must be a safe Google Contacts pagination token")
        return value.strip()

    @classmethod
    def _contact_payload(cls, arguments: dict[str, Any]) -> dict[str, Any]:
        given_name = arguments.get("given_name")
        family_name = arguments.get("family_name")
        if not isinstance(given_name, str) or not 1 <= len(given_name.strip()) <= 200:
            raise ValueError("crm.contact.create requires a given_name of 1-200 characters")
        if family_name is not None and (
            not isinstance(family_name, str) or len(family_name.strip()) > 200
        ):
            raise ValueError("family_name must be 200 characters or fewer")

        payload: dict[str, Any] = {
            "names": [{
                "givenName": given_name.strip(),
                **({"familyName": family_name.strip()} if isinstance(family_name, str) and family_name.strip() else {}),
            }]
        }

        email = arguments.get("email")
        if email is not None:
            if not isinstance(email, str) or not _EMAIL_RE.fullmatch(email.strip()):
                raise ValueError("email must be a valid contact email")
            payload["emailAddresses"] = [{"value": email.strip()}]

        phone = arguments.get("phone")
        if phone is not None:
            if (
                not isinstance(phone, str)
                or not 3 <= len(phone.strip()) <= 64
                or any(ord(char) < 0x20 for char in phone)
            ):
                raise ValueError("phone must be a safe contact phone number")
            payload["phoneNumbers"] = [{"value": phone.strip()}]

        organization = arguments.get("organization")
        if organization is not None:
            if not isinstance(organization, str) or not 1 <= len(organization.strip()) <= 200:
                raise ValueError("organization must be 1-200 characters")
            payload["organizations"] = [{"name": organization.strip()}]
        return payload

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> object:
        record = self._connection_store.get(IntegrationProvider.GOOGLE_CONTACTS.value)
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect Google Contacts.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[IntegrationProvider.GOOGLE_CONTACTS.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.request(
                    method,
                    url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        **({"Content-Type": "application/json"} if json is not None else {}),
                    },
                    json=json,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Google rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Google People API returned HTTP {response.status_code}")
            if not response.content:
                return {"status_code": response.status_code}
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Google People API returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Google People API returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Google People API request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Google People API request failed: {type(exc).__name__}") from exc
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
