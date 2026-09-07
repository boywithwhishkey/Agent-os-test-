from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

_BASE_URL = "https://graph.microsoft.com/v1.0"


class MicrosoftTodoOAuthAdapter(IntegrationAdapter):
    """Governed Microsoft To Do task reads and approval-gated creation."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.MICROSOFT_TODO,
            request,
            reason="Microsoft To Do actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/me", params={"$select": "id,displayName,userPrincipalName"})
        if capability_id == "productivity.task.list":
            list_id = self._identifier(arguments.get("tasklist_id"), "tasklist_id")
            return await self._request(
                "GET",
                f"/me/todo/lists/{quote(list_id, safe='')}/tasks",
                params={"$top": str(self._limit(arguments))},
            )
        if capability_id == "productivity.task.create":
            list_id = self._identifier(arguments.get("tasklist_id"), "tasklist_id")
            return await self._request(
                "POST",
                f"/me/todo/lists/{quote(list_id, safe='')}/tasks",
                json=self._task_payload(arguments),
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 25)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("productivity.task.list limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _identifier(value: object, field: str) -> str:
        if (
            not isinstance(value, str)
            or not 1 <= len(value.strip()) <= 500
            or any(ord(char) < 32 for char in value)
        ):
            raise ValueError(f"{field} must be a safe Microsoft To Do identifier")
        return value.strip()

    @classmethod
    def _task_payload(cls, arguments: dict[str, Any]) -> dict[str, Any]:
        title = arguments.get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 255:
            raise ValueError("productivity.task.create requires a title of 255 characters or fewer")
        payload: dict[str, Any] = {"title": title.strip()}
        body = arguments.get("body", arguments.get("notes"))
        if body is not None:
            if not isinstance(body, str) or len(body) > 10_000:
                raise ValueError("task body must be 10000 characters or fewer")
            payload["body"] = {"contentType": "text", "content": body}
        due = arguments.get("due")
        if due is not None:
            if not isinstance(due, str) or not 1 <= len(due) <= 100:
                raise ValueError("task due must be a bounded ISO-8601 date-time")
            try:
                datetime.fromisoformat(due)
            except ValueError as exc:
                raise ValueError("task due must be a valid ISO-8601 date-time") from exc
            payload["dueDateTime"] = {"dateTime": due, "timeZone": arguments.get("timezone", "UTC")}
        return payload

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> object:
        record = self._connection_store.get(IntegrationProvider.MICROSOFT_TODO.value)
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Microsoft To Do account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS[IntegrationProvider.MICROSOFT_TODO.value],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.request(
                    method,
                    f"{_BASE_URL}{path}",
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
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
