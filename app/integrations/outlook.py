from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import verify_oauth_identity

_BASE_URL = "https://graph.microsoft.com/v1.0"
_EMAIL_RE = re.compile(r"^[^@\s]{1,128}@[^@\s]{1,255}\.[^@\s]{2,63}$")


class OutlookOAuthAdapter(IntegrationAdapter):
    """Governed Microsoft Graph mail and calendar operations."""

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
            IntegrationProvider.OUTLOOK,
            request,
            reason="Outlook actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/me", params={"$select": "id,displayName,userPrincipalName"})
        if capability_id == "mail.message.list":
            limit = self._limit(arguments)
            return await self._request(
                "GET",
                "/me/messages",
                params={
                    "$top": str(limit),
                    "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
                    "$orderby": "receivedDateTime DESC",
                },
                headers={"Prefer": "outlook.body-content-type= text"},
            )
        if capability_id == "mail.message.read":
            message_id = self._id(arguments.get("message_id"), "message_id")
            return await self._request(
                "GET",
                f"/me/messages/{quote(message_id, safe='')}",
                params={"$select": "id,subject,from,toRecipients,receivedDateTime,body,isRead"},
                headers={"Prefer": "outlook.body-content-type= text"},
            )
        if capability_id == "mail.message.send":
            return await self._send_message(arguments)
        if capability_id == "calendar.event.list":
            limit = self._limit(arguments)
            return await self._request(
                "GET",
                "/me/events",
                params={"$top": str(limit), "$select": "id,subject,start,end,location,isAllDay"},
                headers={"Prefer": "outlook.timezone=UTC"},
            )
        if capability_id == "calendar.event.create":
            return await self._create_event(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _send_message(self, arguments: dict[str, Any]) -> object:
        subject = arguments.get("subject")
        body = arguments.get("body", arguments.get("text"))
        recipients = arguments.get("to")
        if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 300:
            raise ValueError("mail.message.send requires a subject of 1-300 characters")
        if not isinstance(body, str) or not 1 <= len(body) <= 50_000:
            raise ValueError("mail.message.send requires body text up to 50000 characters")
        if isinstance(recipients, str):
            recipients = [recipients]
        if (
            not isinstance(recipients, list)
            or not 1 <= len(recipients) <= 50
            or any(not isinstance(email, str) or not _EMAIL_RE.fullmatch(email.strip()) for email in recipients)
        ):
            raise ValueError("mail.message.send requires 1-50 valid recipients")
        payload = {
            "message": {
                "subject": subject.strip(),
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [
                    {"emailAddress": {"address": email.strip()}} for email in recipients
                ],
            }
        }
        return await self._request("POST", "/me/sendMail", json=payload)

    async def _create_event(self, arguments: dict[str, Any]) -> object:
        subject = arguments.get("subject")
        start = arguments.get("start")
        end = arguments.get("end")
        timezone = arguments.get("timezone", "UTC")
        if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 300:
            raise ValueError("calendar.event.create requires a subject of 1-300 characters")
        for name, value in (("start", start), ("end", end)):
            if not isinstance(value, str) or len(value) > 100:
                raise ValueError(f"{name} must be an ISO-8601 date-time")
            try:
                datetime.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{name} must be an ISO-8601 date-time") from exc
        if not isinstance(timezone, str) or not 1 <= len(timezone.strip()) <= 100:
            raise ValueError("timezone must be 1-100 characters")
        payload: dict[str, Any] = {
            "subject": subject.strip(),
            "start": {"dateTime": start, "timeZone": timezone.strip()},
            "end": {"dateTime": end, "timeZone": timezone.strip()},
        }
        location = arguments.get("location")
        if location is not None:
            if not isinstance(location, str) or len(location) > 500:
                raise ValueError("location must be 500 characters or fewer")
            payload["location"] = {"displayName": location}
        return await self._request("POST", "/me/calendar/events", json=payload)

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 25)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _id(value: object, field: str) -> str:
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 500 or any(ord(char) < 32 for char in value):
            raise ValueError(f"{field} must be a safe Microsoft Graph identifier")
        return value.strip()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> object:
        record = self._connection_store.get("outlook")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Microsoft Outlook account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        request_headers = {"Authorization": f"Bearer {record.access_token}"}
        if json is not None:
            request_headers["Content-Type"] = "application/json"
        request_headers.update(headers or {})
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["outlook"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.request(
                    method,
                    f"{_BASE_URL}{path}",
                    params=params,
                    headers={**request_headers, "Authorization": f"Bearer {token}"},
                    json=json,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Microsoft Graph rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Microsoft Graph returned HTTP {response.status_code}")
            if not response.content:
                return {"status_code": response.status_code}
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Microsoft Graph returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Microsoft Graph returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Microsoft Graph request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Microsoft Graph request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        return await verify_oauth_identity(
            provider_id="outlook",
            provider_name="Microsoft Outlook",
            identity_url=f"{_BASE_URL}/me",
            connection_store=self._connection_store,
            build_headers=lambda token: {"Authorization": f"Bearer {token}"},
            client=self._client,
        )
