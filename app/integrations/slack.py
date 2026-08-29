from __future__ import annotations

import httpx

from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import verify_oauth_identity


def _interpret_slack_response(response: httpx.Response) -> tuple[bool, str | None]:
    # Slack's Web API always answers HTTP 200 — success/failure is only in
    # the JSON body (`{"ok": true, ...}` or `{"ok": false, "error": "..."}`).
    try:
        body = response.json()
    except ValueError:
        return False, f"Slack returned a non-JSON response (HTTP {response.status_code})"
    if body.get("ok"):
        return True, None
    return False, f"Slack rejected the stored token ({body.get('error', 'unknown_error')})"


class SlackOAuthAdapter(IntegrationAdapter):
    """Verifies a stored Slack OAuth token via `auth.test` — a free,
    read-only identity check. The token is obtained through the separate
    authorize/callback OAuth flow (see app/integrations/oauth/)."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SLACK,
            request,
            reason="Slack actions (posting messages) are not yet wired to a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        return await verify_oauth_identity(
            provider_id="slack",
            provider_name="Slack",
            identity_url="https://slack.com/api/auth.test",
            connection_store=self._connection_store,
            build_headers=lambda token: {"Authorization": f"Bearer {token}"},
            interpret=_interpret_slack_response,
            client=self._client,
        )
