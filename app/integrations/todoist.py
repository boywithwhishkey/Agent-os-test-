from __future__ import annotations

import re
import time
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

_BASE_URL = "https://api.todoist.com/api/v1"
_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


class TodoistAdapter(IntegrationAdapter):
    """Governed Todoist task listing and creation.

    The token is server configuration, and the adapter only addresses the
    fixed Todoist v1 task routes. Task creation is a WRITE capability, so the
    ConnectorBroker's approval and audit path must allow it first.
    """

    def __init__(
        self,
        *,
        api_token: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_token = api_token or settings.connector_credential(
            "TODOIST_API_TOKEN", settings.todoist_api_token
        ) or ""
        self._client = client
        if not self.api_token.strip():
            raise RuntimeError("TODOIST_API_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.TODOIST,
            request,
            reason="Todoist actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "productivity.task.list":
            return await self._list_tasks(arguments)
        if capability_id == "productivity.task.create":
            return await self._create_task(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _list_tasks(self, arguments: dict[str, Any]) -> object:
        limit = self._limit(arguments)
        params: dict[str, str | int] = {"limit": limit}
        cursor = arguments.get("cursor")
        if cursor is not None:
            if not isinstance(cursor, str) or not 1 <= len(cursor.strip()) <= 2000:
                raise ValueError("productivity.task.list cursor must be 1-2000 characters")
            params["cursor"] = cursor.strip()
        for key in ("project_id", "section_id"):
            value = arguments.get(key)
            if value is not None:
                params[key] = self._id(value, key)
        return await self._request("GET", "/tasks", params=params)

    async def _create_task(self, arguments: dict[str, Any]) -> object:
        content = arguments.get("content")
        if not isinstance(content, str) or not 1 <= len(content.strip()) <= 500:
            raise ValueError("productivity.task.create requires content of 1-500 characters")
        payload: dict[str, Any] = {"content": content.strip()}
        description = arguments.get("description")
        if description is not None:
            if not isinstance(description, str) or len(description) > 5_000:
                raise ValueError("description must be 5000 characters or fewer")
            payload["description"] = description
        for key in ("project_id", "section_id", "parent_id"):
            value = arguments.get(key)
            if value is not None:
                payload[key] = self._id(value, key)
        priority = arguments.get("priority")
        if priority is not None:
            if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 4:
                raise ValueError("priority must be an integer between 1 and 4")
            payload["priority"] = priority
        due_string = arguments.get("due_string")
        if due_string is not None:
            if not isinstance(due_string, str) or not 1 <= len(due_string.strip()) <= 200:
                raise ValueError("due_string must be 1-200 characters")
            payload["due_string"] = due_string.strip()
        labels = arguments.get("labels")
        if labels is not None:
            if (
                not isinstance(labels, list)
                or len(labels) > 20
                or any(not isinstance(label, str) or not 1 <= len(label.strip()) <= 50 for label in labels)
            ):
                raise ValueError("labels must contain at most 20 short strings")
            payload["labels"] = [label.strip() for label in labels]
        return await self._request("POST", "/tasks", json=payload, idempotency_key=str(uuid.uuid4()))

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 50)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _id(value: object, field: str) -> str:
        if not isinstance(value, str) or not _ID_RE.fullmatch(value.strip()):
            raise ValueError(f"{field} must be a safe Todoist identifier")
        return value.strip()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> object:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        headers = {"Authorization": f"Bearer {self.api_token}"}
        if json is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["X-Request-Id"] = idempotency_key
        try:
            response = await client.request(
                method,
                f"{_BASE_URL}{path}",
                params=params,
                json=json,
                headers=headers,
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                if response.status_code == 204:
                    return {"ok": True}
                raise RuntimeError("Todoist returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Todoist returned HTTP {response.status_code}")
            if not isinstance(body, (dict, list)):
                raise TypeError("Todoist returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Todoist request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Todoist request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._list_tasks({"limit": 1})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
