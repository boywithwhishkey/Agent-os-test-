from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

_IDENTITY_ENDPOINTS = {
    IntegrationProvider.GMAIL: "https://gmail.googleapis.com/gmail/v1/users/me/profile",
    IntegrationProvider.GOOGLE_CALENDAR: (
        "https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1"
    ),
    IntegrationProvider.GOOGLE_DRIVE: (
        "https://www.googleapis.com/drive/v3/about?fields=user"
    ),
}


class GoogleOAuthAdapter(IntegrationAdapter):
    """Read-only Google API operations using a stored OAuth access token.

    OAuth authorization and token exchange are deliberately handled by the
    shared routes in ``app/integrations/oauth``. This adapter only consumes a
    token that has already been recorded by that flow and never accepts an
    arbitrary endpoint from workflow arguments.
    """

    def __init__(
        self,
        *,
        provider: IntegrationProvider,
        connection_store: OAuthConnectionStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if provider not in _IDENTITY_ENDPOINTS:
            raise ValueError(f"Unsupported Google provider: {provider}")
        self.provider = provider
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            self.provider,
            request,
            reason=(
                f"{self.provider_name} mutations are not enabled; use governed read capabilities."
            ),
        )

    @property
    def provider_name(self) -> str:
        return {
            IntegrationProvider.GMAIL: "Gmail",
            IntegrationProvider.GOOGLE_CALENDAR: "Google Calendar",
            IntegrationProvider.GOOGLE_DRIVE: "Google Drive",
        }[self.provider]

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get(_IDENTITY_ENDPOINTS[self.provider])

        if self.provider is IntegrationProvider.GMAIL and capability_id == "mail.message.list":
            return await self._get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                params=self._limit_params(arguments),
            )

        if self.provider is IntegrationProvider.GMAIL and capability_id == "mail.draft.create":
            return await self._post(
                "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
                {"message": {"raw": self._draft_raw(arguments)}},
            )

        if (
            self.provider is IntegrationProvider.GOOGLE_CALENDAR
            and capability_id == "calendar.event.list"
        ):
            params = {"maxResults": str(self._max_results(arguments))}
            if isinstance(arguments.get("time_min"), str) and arguments["time_min"].strip():
                params["timeMin"] = arguments["time_min"].strip()
            if isinstance(arguments.get("time_max"), str) and arguments["time_max"].strip():
                params["timeMax"] = arguments["time_max"].strip()
            params.update({"singleEvents": "true", "orderBy": "startTime"})
            return await self._get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                params=params,
            )

        if (
            self.provider is IntegrationProvider.GOOGLE_CALENDAR
            and capability_id == "calendar.event.create"
        ):
            calendar_id, payload = self._event_payload(arguments)
            return await self._post(
                f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events",
                payload,
            )

        if (
            self.provider is IntegrationProvider.GOOGLE_CALENDAR
            and capability_id == "calendar.event.update"
        ):
            calendar_id, event_id, payload = self._event_update_payload(arguments)
            return await self._patch(
                f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events/{quote(event_id, safe='')}",
                payload,
            )

        if (
            self.provider is IntegrationProvider.GOOGLE_CALENDAR
            and capability_id == "calendar.event.delete"
        ):
            calendar_id, event_id = self._event_identifier(arguments)
            await self._delete(
                f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events/{quote(event_id, safe='')}"
            )
            return {"provider": self.provider.value, "event_id": event_id, "deleted": True}

        if self.provider is IntegrationProvider.GOOGLE_DRIVE and capability_id == "files.file.list":
            return await self._get(
                "https://www.googleapis.com/drive/v3/files",
                params={
                    "pageSize": str(self._max_results(arguments)),
                    "fields": "files(id,name,mimeType,modifiedTime)",
                },
            )

        if self.provider is IntegrationProvider.GOOGLE_DRIVE and capability_id == "files.file.write":
            metadata, content, mime_type = self._file_payload(arguments)
            return await self._post_multipart(
                "https://www.googleapis.com/upload/drive/v3/files",
                metadata=metadata,
                content=content,
                mime_type=mime_type,
            )

        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _max_results(arguments: dict[str, Any]) -> int:
        value = arguments.get("max_results", 25)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("max_results must be an integer between 1 and 100")
        return value

    def _limit_params(self, arguments: dict[str, Any]) -> dict[str, str]:
        params = {"maxResults": str(self._max_results(arguments))}
        query = arguments.get("query")
        if isinstance(query, str) and query.strip():
            params["q"] = query.strip()
        return params

    @staticmethod
    def _draft_raw(arguments: dict[str, Any]) -> str:
        recipients = GoogleOAuthAdapter._recipients(arguments.get("to"), "to")
        cc = GoogleOAuthAdapter._recipients(arguments.get("cc"), "cc", required=False)
        bcc = GoogleOAuthAdapter._recipients(arguments.get("bcc"), "bcc", required=False)
        subject = arguments.get("subject")
        body = arguments.get("body")
        if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 998:
            raise ValueError("mail.draft.create requires a subject of 998 characters or fewer")
        if not isinstance(body, str) or not 1 <= len(body) <= 200_000:
            raise ValueError("mail.draft.create requires a body between 1 and 200000 characters")
        if any("\r" in value or "\n" in value for value in [subject, body]):
            raise ValueError("mail.draft.create subject and body must not contain raw line breaks")

        message = EmailMessage()
        message["To"] = ", ".join(recipients)
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        message["Subject"] = subject.strip()
        message.set_content(body)
        return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")

    @staticmethod
    def _recipients(value: Any, field: str, *, required: bool = True) -> list[str]:
        if value is None and not required:
            return []
        values = [value] if isinstance(value, str) else value
        if not isinstance(values, list) or not values or len(values) > 20:
            raise ValueError(f"mail.draft.create requires 1-20 {field} recipients")
        output: list[str] = []
        for candidate in values:
            if not isinstance(candidate, str) or "\r" in candidate or "\n" in candidate:
                raise ValueError(f"mail.draft.create {field} recipients must be valid email addresses")
            address = parseaddr(candidate.strip())[1]
            if not address or "@" not in address or " " in address:
                raise ValueError(f"mail.draft.create {field} recipients must be valid email addresses")
            output.append(candidate.strip())
        return output

    @staticmethod
    def _file_payload(arguments: dict[str, Any]) -> tuple[dict[str, Any], bytes, str]:
        name = arguments.get("name")
        if (
            not isinstance(name, str)
            or not 1 <= len(name.strip()) <= 255
            or "/" in name
            or "\\" in name
        ):
            raise ValueError("files.file.write requires a file name without path separators")
        mime_type = arguments.get("mime_type", "text/plain")
        if not isinstance(mime_type, str) or not re.fullmatch(r"[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+", mime_type):
            raise ValueError("mime_type must be a valid MIME type")
        content = arguments.get("content")
        if not isinstance(content, str) or not 1 <= len(content.encode("utf-8")) <= 5_000_000:
            raise ValueError("files.file.write requires text content up to 5000000 bytes")
        metadata: dict[str, Any] = {"name": name.strip(), "mimeType": mime_type}
        parent = arguments.get("parent_id")
        if parent is not None:
            if (
                not isinstance(parent, str)
                or not 1 <= len(parent.strip()) <= 200
                or "/" in parent
                or "\\" in parent
            ):
                raise ValueError("parent_id must be a valid Drive folder identifier")
            metadata["parents"] = [parent.strip()]
        return metadata, content.encode("utf-8"), mime_type

    @staticmethod
    def _event_payload(arguments: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        calendar_id = arguments.get("calendar_id", "primary")
        if (
            not isinstance(calendar_id, str)
            or not 1 <= len(calendar_id.strip()) <= 200
            or "/" in calendar_id
            or "\\" in calendar_id
        ):
            raise ValueError("calendar_id must be a non-empty identifier without path separators")

        summary = arguments.get("summary")
        if not isinstance(summary, str) or not 1 <= len(summary.strip()) <= 200:
            raise ValueError("calendar.event.create requires a summary of 200 characters or fewer")

        start = arguments.get("start")
        end = arguments.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            raise TypeError("calendar.event.create requires RFC3339 start and end values")
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
        except ValueError as exc:
            raise ValueError("start and end must be valid RFC3339 date-times") from exc
        if start_dt.tzinfo is None or end_dt.tzinfo is None:
            raise ValueError("start and end must include a timezone offset")
        if end_dt <= start_dt:
            raise ValueError("end must be after start")

        payload: dict[str, Any] = {
            "summary": summary.strip(),
            "start": {"dateTime": start.strip()},
            "end": {"dateTime": end.strip()},
        }
        description = arguments.get("description")
        if description is not None:
            if not isinstance(description, str) or len(description) > 10_000:
                raise ValueError("description must be 10000 characters or fewer")
            payload["description"] = description
        timezone = arguments.get("timezone")
        if timezone is not None:
            if not isinstance(timezone, str) or not 1 <= len(timezone.strip()) <= 100:
                raise ValueError("timezone must be 100 characters or fewer")
            payload["start"]["timeZone"] = timezone.strip()
            payload["end"]["timeZone"] = timezone.strip()
        return calendar_id.strip(), payload

    @staticmethod
    def _event_identifier(arguments: dict[str, Any]) -> tuple[str, str]:
        calendar_id = arguments.get("calendar_id", "primary")
        event_id = arguments.get("event_id")
        if (
            not isinstance(calendar_id, str)
            or not 1 <= len(calendar_id.strip()) <= 200
            or "/" in calendar_id
            or "\\" in calendar_id
        ):
            raise ValueError("calendar_id must be a non-empty identifier without path separators")
        if (
            not isinstance(event_id, str)
            or not 1 <= len(event_id.strip()) <= 1024
            or "/" in event_id
            or "\\" in event_id
        ):
            raise ValueError("event_id must be a non-empty identifier without path separators")
        return calendar_id.strip(), event_id.strip()

    @staticmethod
    def _event_update_payload(arguments: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
        calendar_id, event_id = GoogleOAuthAdapter._event_identifier(arguments)
        _, payload = GoogleOAuthAdapter._event_payload(arguments)
        return calendar_id, event_id, payload

    async def _get(self, url: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        record = self._connection_store.get(self.provider.value)
        if not record.access_token:
            raise RuntimeError(
                f"Not authorized yet — use Authorize to connect a {self.provider_name} account."
            )

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[self.provider.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError(
                        f"{self.provider_name} rejected the stored token (HTTP 401) — authorize again"
                    )
                raise RuntimeError(f"{self.provider_name} returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError(f"{self.provider_name} returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError(f"{self.provider_name} returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"{self.provider_name} request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.provider_name} request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self._connection_store.get(self.provider.value)
        if not record.access_token:
            raise RuntimeError(
                f"Not authorized yet — use Authorize to connect a {self.provider_name} account."
            )

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[self.provider.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError(
                        f"{self.provider_name} rejected the stored token (HTTP 401) — authorize again"
                    )
                raise RuntimeError(f"{self.provider_name} returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError(f"{self.provider_name} returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError(f"{self.provider_name} returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"{self.provider_name} request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.provider_name} request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _patch(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self._connection_store.get(self.provider.value)
        if not record.access_token:
            raise RuntimeError(
                f"Not authorized yet — use Authorize to connect a {self.provider_name} account."
            )
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[self.provider.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.patch(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError(
                        f"{self.provider_name} rejected the stored token (HTTP 401) — authorize again"
                    )
                raise RuntimeError(f"{self.provider_name} returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError(f"{self.provider_name} returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError(f"{self.provider_name} returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"{self.provider_name} request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.provider_name} request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _delete(self, url: str) -> None:
        record = self._connection_store.get(self.provider.value)
        if not record.access_token:
            raise RuntimeError(
                f"Not authorized yet — use Authorize to connect a {self.provider_name} account."
            )
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[self.provider.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.delete(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError(
                        f"{self.provider_name} rejected the stored token (HTTP 401) — authorize again"
                    )
                raise RuntimeError(f"{self.provider_name} returned HTTP {response.status_code}")
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"{self.provider_name} request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.provider_name} request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _post_multipart(
        self,
        url: str,
        *,
        metadata: dict[str, Any],
        content: bytes,
        mime_type: str,
    ) -> dict[str, Any]:
        record = self._connection_store.get(self.provider.value)
        if not record.access_token:
            raise RuntimeError(
                f"Not authorized yet — use Authorize to connect a {self.provider_name} account."
            )

        boundary = "thynact-drive-boundary"
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        ).encode("ascii")
        body += json.dumps(metadata, separators=(",", ":")).encode("utf-8")
        body += (
            f"\r\n--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n"
        ).encode("ascii")
        body += content
        body += f"\r\n--{boundary}--\r\n".encode("ascii")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[self.provider.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    url,
                    params={"uploadType": "multipart", "fields": "id,name,mimeType,size"},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": f"multipart/related; boundary={boundary}",
                    },
                    content=body,
                    timeout=30.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError(
                        f"{self.provider_name} rejected the stored token (HTTP 401) — authorize again"
                    )
                raise RuntimeError(f"{self.provider_name} returned HTTP {response.status_code}")
            try:
                result = response.json()
            except ValueError as exc:
                raise RuntimeError(f"{self.provider_name} returned a non-JSON response") from exc
            if not isinstance(result, dict):
                raise TypeError(f"{self.provider_name} returned an invalid response")
            return result
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"{self.provider_name} request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.provider_name} request failed: {type(exc).__name__}") from exc
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
