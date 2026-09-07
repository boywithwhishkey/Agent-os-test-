from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

_BASE_URL = "https://app.asana.com/api/1.0"
_GID_RE = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


class AsanaAdapter(IntegrationAdapter):
    """Governed Asana task list/create operations scoped to one workspace."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        workspace_gid: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.access_token = access_token or settings.connector_credential(
            "ASANA_ACCESS_TOKEN", settings.asana_access_token
        ) or ""
        self.workspace_gid = workspace_gid or settings.connector_credential(
            "ASANA_WORKSPACE_GID", settings.asana_workspace_gid
        ) or ""
        self._client = client
        if not self.access_token.strip():
            raise RuntimeError("ASANA_ACCESS_TOKEN is required")
        self._validate_gid(self.workspace_gid, "ASANA_WORKSPACE_GID")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.ASANA,
            request,
            reason="Asana actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "productivity.task.list":
            return await self._list_tasks(arguments)
        if capability_id == "productivity.task.create":
            return await self._create_task(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _list_tasks(self, arguments: dict[str, Any]) -> object:
        limit = self._limit(arguments)
        params: dict[str, str | int] = {
            "workspace": self.workspace_gid,
            "assignee": "me",
            "limit": limit,
        }
        for key in ("project", "section"):
            value = arguments.get(key)
            if value is not None:
                params[key] = self._validate_gid(value, key)
        offset = arguments.get("offset")
        if offset is not None:
            if not isinstance(offset, str) or not 1 <= len(offset.strip()) <= 2_000:
                raise ValueError("productivity.task.list offset must be 1-2000 characters")
            params["offset"] = offset.strip()
        return await self._request("GET", "/tasks", params=params)

    async def _create_task(self, arguments: dict[str, Any]) -> object:
        content = arguments.get("content")
        if not isinstance(content, str) or not 1 <= len(content.strip()) <= 500:
            raise ValueError("productivity.task.create requires content of 1-500 characters")
        data: dict[str, Any] = {"name": content.strip(), "workspace": self.workspace_gid}
        description = arguments.get("description")
        if description is not None:
            if not isinstance(description, str) or len(description) > 5_000:
                raise ValueError("description must be 5000 characters or fewer")
            data["notes"] = description
        project = arguments.get("project")
        if project is not None:
            data["projects"] = [self._validate_gid(project, "project")]
        assignee = arguments.get("assignee")
        if assignee is not None:
            if not isinstance(assignee, str) or assignee.strip() not in {"me", ""}:
                data["assignee"] = self._validate_gid(assignee, "assignee")
            elif assignee.strip() == "me":
                data["assignee"] = "me"
        due_on = arguments.get("due_on")
        if due_on is not None:
            if not isinstance(due_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due_on.strip()):
                raise ValueError("due_on must be YYYY-MM-DD")
            data["due_on"] = due_on.strip()
        return await self._request("POST", "/tasks", json={"data": data})

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 50)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _validate_gid(value: object, field: str) -> str:
        if not isinstance(value, str) or not _GID_RE.fullmatch(value.strip()):
            raise ValueError(f"{field} must be a safe Asana GID")
        return value.strip()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
        json: dict[str, Any] | None = None,
    ) -> object:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.request(
                method,
                f"{_BASE_URL}{path}",
                params=params,
                json=json,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Asana returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Asana returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Asana returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Asana request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Asana request failed: {type(exc).__name__}") from exc
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
