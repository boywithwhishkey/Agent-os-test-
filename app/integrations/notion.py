from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import verify_oauth_identity

NOTION_API_VERSION = "2022-06-28"


class NotionOAuthAdapter(IntegrationAdapter):
    """Run fixed, bounded Notion identity, page-read, and page-write operations."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.NOTION,
            request,
            reason="Notion actions (reading/writing pages) are not yet wired to a triggered workflow.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._request("GET", "/users/me")
        if capability_id == "docs.page.read":
            page_id = arguments.get("page_id")
            if page_id is not None:
                return await self._request("GET", f"/pages/{quote(self._page_id(page_id), safe='-')}")
            return await self._search_pages(arguments)
        if capability_id == "docs.page.write":
            return await self._request("POST", "/pages", json=self._page_write_payload(arguments))
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _page_id(value: object, *, operation: str = "docs.page.read") -> str:
        if not isinstance(value, str):
            raise TypeError(f"{operation} page_id must be a Notion page id")
        page_id = value.strip()
        compact = page_id.replace("-", "")
        if len(compact) != 32 or any(char not in "0123456789abcdefABCDEF" for char in compact):
            raise ValueError(f"{operation} page_id must be a Notion page id")
        return page_id

    @staticmethod
    def _page_write_payload(arguments: dict[str, Any]) -> dict[str, Any]:
        parent_page_id = NotionOAuthAdapter._page_id(
            arguments.get("parent_page_id"), operation="docs.page.write"
        )
        title = arguments.get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
            raise ValueError("docs.page.write requires a title of 200 characters or fewer")
        content = arguments.get("content", "")
        if not isinstance(content, str) or len(content) > 20_000:
            raise ValueError("docs.page.write content must be 20000 characters or fewer")
        payload: dict[str, Any] = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": title.strip()}}
                    ]
                }
            },
        }
        if content:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content}}
                        ]
                    },
                }
            ]
        return payload

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 20)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("docs.page.read limit must be an integer between 1 and 100")
        return value

    async def _search_pages(self, arguments: dict[str, Any]) -> dict[str, Any] | list[Any]:
        payload: dict[str, Any] = {
            "page_size": self._limit(arguments),
            "filter": {"property": "object", "value": "page"},
        }
        query = arguments.get("query")
        if query is not None:
            if not isinstance(query, str) or len(query) > 200:
                raise ValueError("docs.page.read query must be 200 characters or fewer")
            if query.strip():
                payload["query"] = query.strip()
        cursor = arguments.get("cursor")
        if cursor is not None:
            if not isinstance(cursor, str) or not cursor.strip() or len(cursor) > 2000:
                raise ValueError("docs.page.read cursor must be a non-empty string of 2000 characters or fewer")
            payload["start_cursor"] = cursor.strip()
        return await self._request("POST", "/search", json=payload)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        record = self._connection_store.get("notion")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a Notion account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["notion"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.request(
                    method,
                    f"https://api.notion.com/v1{path}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Notion-Version": NOTION_API_VERSION,
                        "Content-Type": "application/json",
                    },
                    json=json,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("Notion rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"Notion returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Notion returned a non-JSON response") from exc
            if not isinstance(body, (dict, list)):
                raise TypeError("Notion returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Notion request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Notion request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        return await verify_oauth_identity(
            provider_id="notion",
            provider_name="Notion",
            identity_url="https://api.notion.com/v1/users/me",
            connection_store=self._connection_store,
            build_headers=lambda token: {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_API_VERSION,
            },
            client=self._client,
        )
