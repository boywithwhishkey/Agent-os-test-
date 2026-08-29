from __future__ import annotations

import httpx

from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import verify_oauth_identity

NOTION_API_VERSION = "2022-06-28"


class NotionOAuthAdapter(IntegrationAdapter):
    """Verifies a stored Notion OAuth token via `GET /v1/users/me` — a
    free, read-only identity check. The token is obtained through the
    separate authorize/callback OAuth flow (see app/integrations/oauth/)."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.NOTION,
            request,
            reason="Notion actions (reading/writing pages) are not yet wired to a triggered workflow.",
        )

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
