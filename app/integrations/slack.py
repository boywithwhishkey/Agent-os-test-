from __future__ import annotations

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
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
            reason="Slack actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        if capability_id != "chat.message.send":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        channel = arguments.get("channel")
        text = arguments.get("text", arguments.get("content"))
        if not isinstance(channel, str) or not channel.strip() or len(channel) > 200:
            raise ValueError("chat.message.send requires a Slack channel")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("chat.message.send requires non-empty text or content")
        if len(text) > 40000:
            raise ValueError("Slack message text must be 40000 characters or fewer")

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["slack"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"channel": channel.strip(), "text": text},
                    timeout=10.0,
                ),
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Slack returned a non-JSON response") from exc
            if response.status_code >= 400 or not body.get("ok"):
                raise RuntimeError(f"Slack rejected the message ({body.get('error', f'HTTP {response.status_code}')})")
            return {
                "provider": IntegrationProvider.SLACK.value,
                "channel": body.get("channel", channel.strip()),
                "message_id": body.get("ts"),
            }
        except httpx.TimeoutException as exc:
            raise RuntimeError("Slack request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Slack request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

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
