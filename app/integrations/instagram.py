from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.meta import MetaGraphClient
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class InstagramGraphAdapter(IntegrationAdapter):
    """Governed text operations for one Instagram professional account."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        business_account_id: str | None = None,
        api_version: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        token = access_token or settings.meta_access_token or ""
        account_id = business_account_id or settings.instagram_business_account_id or ""
        if not token.strip():
            raise RuntimeError("META_ACCESS_TOKEN is required")
        if not account_id.strip():
            raise RuntimeError("INSTAGRAM_BUSINESS_ACCOUNT_ID is required")
        self.business_account_id = account_id
        self._graph = MetaGraphClient(
            access_token=token,
            api_version=api_version or settings.meta_graph_api_version,
            client=client,
        )

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.INSTAGRAM,
            request,
            reason="Instagram actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            body, _ = await self._graph.request(
                "GET", self.business_account_id, params={"fields": "id,username,name"}
            )
            return body
        if capability_id == "social.post.publish":
            return await self._publish_image_post(arguments)
        if capability_id != "chat.message.send":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        recipient = arguments.get("recipient_id")
        text = arguments.get("text", arguments.get("content"))
        if not isinstance(recipient, str) or not recipient.strip() or len(recipient) > 128:
            raise ValueError("chat.message.send requires a recipient_id")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("chat.message.send requires non-empty text or content")
        if len(text) > 1000:
            raise ValueError("Instagram message text must be 1000 characters or fewer")
        body, status_code = await self._graph.request(
            "POST",
            f"{self.business_account_id}/messages",
            json={"recipient": {"id": recipient}, "message": {"text": text}},
        )
        return {
            "provider": IntegrationProvider.INSTAGRAM.value,
            "status_code": status_code,
            "message_id": body.get("message_id"),
        }

    async def _publish_image_post(self, arguments: dict[str, Any]) -> object:
        image_url = arguments.get("image_url")
        if not isinstance(image_url, str) or not self._is_public_https_url(image_url):
            raise ValueError("social.post.publish requires an HTTPS image_url")
        if len(image_url) > 2048:
            raise ValueError("social.post.publish image_url must be 2048 characters or fewer")
        caption = arguments.get("caption", "")
        if not isinstance(caption, str) or len(caption) > 2200:
            raise ValueError("Instagram captions must be 2200 characters or fewer")

        container_params = {"image_url": image_url}
        if caption.strip():
            container_params["caption"] = caption
        container, container_status = await self._graph.request(
            "POST",
            f"{self.business_account_id}/media",
            params=container_params,
        )
        creation_id = container.get("id")
        if not isinstance(creation_id, str) or not creation_id.strip():
            raise RuntimeError("Instagram did not return a media container id")
        published, publish_status = await self._graph.request(
            "POST",
            f"{self.business_account_id}/media_publish",
            params={"creation_id": creation_id},
        )
        media_id = published.get("id")
        if not isinstance(media_id, str) or not media_id.strip():
            raise RuntimeError("Instagram did not return a published media id")
        return {
            "provider": IntegrationProvider.INSTAGRAM.value,
            "container_status_code": container_status,
            "publish_status_code": publish_status,
            "container_id": creation_id,
            "media_id": media_id,
        }

    @staticmethod
    def _is_public_https_url(value: str) -> bool:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and parsed.hostname.lower() not in {"localhost", "127.0.0.1", "::1"}
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
