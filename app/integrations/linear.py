from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class LinearAdapter(IntegrationAdapter):
    """Run bounded Linear GraphQL identity, issue, and governed mutations."""

    _IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.linear_api_key or ""
        self._client = client
        if not self.api_key.strip():
            raise RuntimeError("LINEAR_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.LINEAR,
            request,
            reason="Linear actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._query("query { viewer { id name email } }")
        if capability_id == "tracker.issue.list":
            return await self._query(
                "query { issues(first: 50) { nodes { id identifier title state { name } } } }"
            )
        if capability_id == "tracker.issue.create":
            payload = self._issue_create_payload(arguments)
            data = await self._query(
                """
                mutation IssueCreate($input: IssueCreateInput!) {
                  issueCreate(input: $input) {
                    success
                    issue { id identifier title state { id name } }
                  }
                }
                """,
                variables={"input": payload},
            )
            return self._mutation_data(data, "issueCreate")
        if capability_id == "tracker.issue.update":
            issue_id = self._identifier(arguments, "issue_id", "tracker.issue.update")
            payload = self._issue_update_payload(arguments)
            data = await self._query(
                """
                mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
                  issueUpdate(id: $id, input: $input) {
                    success
                    issue { id identifier title state { id name } }
                  }
                }
                """,
                variables={"id": issue_id, "input": payload},
            )
            return self._mutation_data(data, "issueUpdate")
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @classmethod
    def _identifier(cls, arguments: dict[str, Any], key: str, capability: str) -> str:
        value = arguments.get(key)
        if not isinstance(value, str) or not cls._IDENTIFIER.fullmatch(value.strip()):
            raise ValueError(f"{capability} requires a valid {key}")
        return value.strip()

    @staticmethod
    def _title(arguments: dict[str, Any], *, required: bool) -> str | None:
        value = arguments.get("title")
        if value is None and not required:
            return None
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 255:
            raise ValueError("title must be non-empty and 255 characters or fewer")
        return value.strip()

    @staticmethod
    def _description(arguments: dict[str, Any]) -> str:
        value = arguments.get("description")
        if not isinstance(value, str) or len(value) > 10_000:
            raise ValueError("description must be a string of 10000 characters or fewer")
        return value

    @classmethod
    def _issue_create_payload(cls, arguments: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "teamId": cls._identifier(arguments, "team_id", "tracker.issue.create"),
            "title": cls._title(arguments, required=True),
        }
        if "description" in arguments:
            payload["description"] = cls._description(arguments)
        if "state_id" in arguments:
            payload["stateId"] = cls._identifier(arguments, "state_id", "tracker.issue.create")
        return payload

    @classmethod
    def _issue_update_payload(cls, arguments: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if "title" in arguments:
            payload["title"] = cls._title(arguments, required=True)
        if "description" in arguments:
            payload["description"] = cls._description(arguments)
        if "state_id" in arguments:
            payload["stateId"] = cls._identifier(arguments, "state_id", "tracker.issue.update")
        if not payload:
            raise ValueError("tracker.issue.update requires title, description, or state_id")
        return payload

    @staticmethod
    def _mutation_data(data: dict[str, Any], mutation: str) -> dict[str, Any]:
        payload = data.get(mutation)
        if not isinstance(payload, dict) or payload.get("success") is not True:
            raise RuntimeError(f"Linear {mutation} did not succeed")
        return data

    async def _query(
        self,
        query: str,
        *,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                "https://api.linear.app/graphql",
                json={"query": query, **({"variables": variables} if variables is not None else {})},
                headers={"Authorization": self.api_key, "Content-Type": "application/json"},
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Linear returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Linear returned HTTP {response.status_code}")
            if not isinstance(body, dict) or body.get("errors"):
                raise RuntimeError("Linear GraphQL returned an error")
            data = body.get("data")
            if not isinstance(data, dict):
                raise TypeError("Linear returned an invalid GraphQL response")
            return data
        except httpx.TimeoutException as exc:
            raise RuntimeError("Linear request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Linear request failed: {type(exc).__name__}") from exc
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
