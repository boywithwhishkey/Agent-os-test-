from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import verify_oauth_identity

_BASE_URL = "https://api.zoom.us/v2"


class ZoomOAuthAdapter(IntegrationAdapter):
    """Governed Zoom meeting operations through a stored OAuth connection."""

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
            IntegrationProvider.ZOOM,
            request,
            reason="Zoom actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/users/me")
        if capability_id == "meeting.session.list":
            limit = self._limit(arguments)
            params = {"page_size": str(limit), "type": "scheduled"}
            cursor = arguments.get("next_page_token")
            if cursor is not None:
                if not isinstance(cursor, str) or not 1 <= len(cursor.strip()) <= 512:
                    raise ValueError("meeting.session.list next_page_token must be 1-512 characters")
                params["next_page_token"] = cursor.strip()
            return await self._request("GET", "/users/me/meetings", params=params)
        if capability_id == "meeting.session.create":
            return await self._create_meeting(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _create_meeting(self, arguments: dict[str, Any]) -> object:
        topic = arguments.get("topic")
        if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 200:
            raise ValueError("meeting.session.create requires a topic of 1-200 characters")
        start_time = arguments.get("start_time")
        if not isinstance(start_time, str) or len(start_time) > 100:
            raise ValueError("start_time must be an ISO-8601 date-time")
        try:
            parsed = datetime.fromisoformat(start_time)
        except ValueError as exc:
            raise ValueError("start_time must be an ISO-8601 date-time") from exc
        if parsed.tzinfo is None:
            raise ValueError("start_time must include a timezone offset")
        duration = arguments.get("duration", 30)
        if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 1_440:
            raise ValueError("duration must be an integer between 1 and 1440 minutes")
        payload: dict[str, Any] = {
            "topic": topic.strip(),
            "type": 2,
            "start_time": start_time,
            "duration": duration,
        }
        timezone = arguments.get("timezone")
        if timezone is not None:
            if not isinstance(timezone, str) or not 1 <= len(timezone.strip()) <= 100:
                raise ValueError("timezone must be 1-100 characters")
            payload["timezone"] = timezone.strip()
        agenda = arguments.get("agenda")
        if agenda is not None:
            if not isinstance(agenda, str) or len(agenda) > 2_000:
                raise ValueError("agenda must be 2000 characters or fewer")
            payload["agenda"] = agenda
        return await self._request("POST", "/users/me/meetings", json=payload)

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 30)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> object:
        record = self._connection_store.get("zoom")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Zoom account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        headers = {"Authorization": f"Bearer {record.access_token}"}
        if json is not None:
            headers["Content-Type"] = "application/json"
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["zoom"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.request(
                    method,
                    f"{_BASE_URL}{path}",
                    params=params,
                    headers={**headers, "Authorization": f"Bearer {token}"},
                    json=json,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Zoom rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Zoom returned HTTP {response.status_code}")
            if not response.content:
                return {"status_code": response.status_code}
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Zoom returned a non-JSON response") from exc
            if not isinstance(body, dict):
                raise TypeError("Zoom returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Zoom request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Zoom request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        return await verify_oauth_identity(
            provider_id="zoom",
            provider_name="Zoom",
            identity_url=f"{_BASE_URL}/users/me",
            connection_store=self._connection_store,
            build_headers=lambda token: {"Authorization": f"Bearer {token}"},
            client=self._client,
        )
