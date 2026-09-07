from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

_BASE_URL = "https://api.trello.com/1"
_ID_RE = re.compile(r"^[A-Za-z0-9]{1,64}$")


class TrelloAdapter(IntegrationAdapter):
    """Governed Trello card operations scoped to one configured board/list."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        token: str | None = None,
        board_id: str | None = None,
        list_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or settings.connector_credential(
            "TRELLO_API_KEY", settings.trello_api_key
        ) or ""
        self.token = token or settings.connector_credential(
            "TRELLO_TOKEN", settings.trello_token
        ) or ""
        self.board_id = self._validate_id(
            board_id or settings.connector_credential("TRELLO_BOARD_ID", settings.trello_board_id),
            "TRELLO_BOARD_ID",
        )
        self.list_id = self._validate_id(
            list_id or settings.connector_credential("TRELLO_LIST_ID", settings.trello_list_id),
            "TRELLO_LIST_ID",
        )
        self._client = client
        if not self.api_key.strip():
            raise RuntimeError("TRELLO_API_KEY is required")
        if not self.token.strip():
            raise RuntimeError("TRELLO_TOKEN is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.TRELLO,
            request,
            reason="Trello actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request(
                "GET",
                "/members/me",
                params={"fields": "id,fullName,username,url"},
            )
        if capability_id == "productivity.task.list":
            return await self._list_cards(arguments)
        if capability_id == "productivity.task.create":
            return await self._create_card(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _list_cards(self, arguments: dict[str, Any]) -> object:
        limit = self._limit(arguments)
        body = await self._request(
            "GET",
            f"/boards/{self.board_id}/cards",
            params={"fields": "id,name,desc,due,idList,url", "filter": "open"},
        )
        if not isinstance(body, list):
            raise TypeError("Trello returned an invalid cards response")
        return {
            "provider": IntegrationProvider.TRELLO.value,
            "cards": body[:limit],
            "truncated": len(body) > limit,
        }

    async def _create_card(self, arguments: dict[str, Any]) -> object:
        name = arguments.get("content", arguments.get("name"))
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 500:
            raise ValueError("productivity.task.create requires content of 1-500 characters")
        params: dict[str, str] = {"idList": self.list_id, "name": name.strip(), "pos": "top"}
        description = arguments.get("description")
        if description is not None:
            if not isinstance(description, str) or len(description) > 10_000:
                raise ValueError("description must be 10000 characters or fewer")
            params["desc"] = description
        due = arguments.get("due")
        if due is not None:
            if not isinstance(due, str) or len(due) > 100:
                raise ValueError("due must be an ISO-8601 date-time")
            try:
                datetime.fromisoformat(due)
            except ValueError as exc:
                raise ValueError("due must be an ISO-8601 date-time") from exc
            params["due"] = due
        return await self._request("POST", "/cards", params=params)

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 25)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    @staticmethod
    def _validate_id(value: object, field: str) -> str:
        if not isinstance(value, str) or not _ID_RE.fullmatch(value.strip()):
            raise RuntimeError(f"{field} is required and must be a safe Trello identifier")
        return value.strip()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> object:
        query = {"key": self.api_key, "token": self.token, **(params or {})}
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.request(
                method,
                f"{_BASE_URL}{path}",
                params=query,
                headers={"Accept": "application/json"},
                timeout=10.0,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Trello returned HTTP {response.status_code}")
            if not response.content:
                return {"status_code": response.status_code}
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Trello returned a non-JSON response") from exc
            if not isinstance(body, (dict, list)):
                raise TypeError("Trello returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Trello request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Trello request failed: {type(exc).__name__}") from exc
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
