from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.meta import MetaGraphClient
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class WhatsAppCloudAdapter(IntegrationAdapter):
    """Governed text operations for one WhatsApp Cloud phone number."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        token = access_token or settings.meta_access_token or ""
        phone_id = phone_number_id or settings.whatsapp_phone_number_id or ""
        if not token.strip():
            raise RuntimeError("META_ACCESS_TOKEN is required")
        if not phone_id.strip():
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID is required")
        self.phone_number_id = phone_id
        self._graph = MetaGraphClient(
            access_token=token,
            api_version=api_version or settings.meta_graph_api_version,
            client=client,
        )

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.WHATSAPP,
            request,
            reason="WhatsApp actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            body, _ = await self._graph.request(
                "GET", self.phone_number_id, params={"fields": "id,display_phone_number,verified_name"}
            )
            return body
        if capability_id != "chat.message.send":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        recipient = arguments.get("to")
        text = arguments.get("text", arguments.get("content"))
        if not isinstance(recipient, str) or not recipient.strip() or len(recipient) > 32:
            raise ValueError("chat.message.send requires a recipient phone number")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("chat.message.send requires non-empty text or content")
        if len(text) > 4096:
            raise ValueError("WhatsApp text must be 4096 characters or fewer")
        body, status_code = await self._graph.request(
            "POST",
            f"{self.phone_number_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            },
        )
        messages = body.get("messages") or []
        return {
            "provider": IntegrationProvider.WHATSAPP.value,
            "status_code": status_code,
            "message_id": messages[0].get("id") if messages else None,
        }

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
