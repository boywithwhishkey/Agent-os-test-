from __future__ import annotations

from typing import Any

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
    """Run fixed, governed Slack operations with a stored OAuth token.

    Authorization and token exchange are handled by the shared OAuth routes;
    this adapter only accepts canonical capabilities and never accepts an
    arbitrary Slack method or URL from a workflow.
    """

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SLACK,
            request,
            reason="Slack actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "chat.channel.list":
            return await self._list_channels(arguments)
        if capability_id == "chat.message.list":
            return await self._list_messages(arguments)
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

    async def _list_messages(self, arguments: dict[str, Any]) -> object:
        channel = arguments.get("channel")
        if not isinstance(channel, str) or not channel.strip() or len(channel) > 200:
            raise ValueError("chat.message.list requires a Slack channel")
        limit = arguments.get("limit", 20)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("chat.message.list limit must be an integer between 1 and 100")
        cursor = arguments.get("cursor")
        if cursor is not None and (
            not isinstance(cursor, str) or not cursor.strip() or len(cursor) > 2000
        ):
            raise ValueError("chat.message.list cursor must be a non-empty string of 2000 characters or fewer")

        params = {"channel": channel.strip(), "limit": str(limit)}
        if cursor is not None:
            params["cursor"] = cursor.strip()

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["slack"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    "https://slack.com/api/conversations.history",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Slack returned a non-JSON response") from exc
            if response.status_code >= 400 or not body.get("ok"):
                raise RuntimeError(
                    f"Slack rejected the message list ({body.get('error', f'HTTP {response.status_code}')})"
                )
            messages = body.get("messages", [])
            if not isinstance(messages, list):
                raise TypeError("Slack returned an invalid message list")
            metadata = body.get("response_metadata") or {}
            next_cursor = metadata.get("next_cursor") if isinstance(metadata, dict) else None
            return {
                "provider": IntegrationProvider.SLACK.value,
                "channel": body.get("channel", channel.strip()),
                "messages": messages,
                "has_more": bool(body.get("has_more", False)),
                "next_cursor": next_cursor or None,
            }
        except httpx.TimeoutException as exc:
            raise RuntimeError("Slack request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Slack request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _list_channels(self, arguments: dict[str, Any]) -> object:
        limit = arguments.get("limit", 20)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("chat.channel.list limit must be an integer between 1 and 100")
        cursor = arguments.get("cursor")
        if cursor is not None and (
            not isinstance(cursor, str) or not cursor.strip() or len(cursor) > 2000
        ):
            raise ValueError("chat.channel.list cursor must be a non-empty string of 2000 characters or fewer")
        types = arguments.get("types", "public_channel")
        if not isinstance(types, str) or not types.strip():
            raise ValueError("chat.channel.list types must be a non-empty comma-separated string")
        allowed_types = {"public_channel", "private_channel", "mpim", "im"}
        requested_types = [item.strip() for item in types.split(",") if item.strip()]
        if not requested_types or any(item not in allowed_types for item in requested_types):
            raise ValueError("chat.channel.list types contains an unsupported conversation type")
        if len(set(requested_types)) != len(requested_types):
            raise ValueError("chat.channel.list types must not contain duplicates")

        params = {
            "limit": str(limit),
            "exclude_archived": "true",
            "types": ",".join(requested_types),
        }
        if cursor is not None:
            params["cursor"] = cursor.strip()

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["slack"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    "https://slack.com/api/conversations.list",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                ),
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Slack returned a non-JSON response") from exc
            if response.status_code >= 400 or not body.get("ok"):
                raise RuntimeError(
                    f"Slack rejected the channel list ({body.get('error', f'HTTP {response.status_code}')})"
                )
            channels = body.get("channels", [])
            if not isinstance(channels, list):
                raise TypeError("Slack returned an invalid channel list")
            metadata = body.get("response_metadata") or {}
            next_cursor = metadata.get("next_cursor") if isinstance(metadata, dict) else None
            return {
                "provider": IntegrationProvider.SLACK.value,
                "channels": channels,
                "has_more": bool(body.get("has_more", False)),
                "next_cursor": next_cursor or None,
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
