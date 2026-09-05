from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


class WebhookPayloadError(ValueError):
    """Raised when a verified provider body cannot be normalized safely."""


class WebhookEvent(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=128)
    event_id: str = Field(min_length=1, max_length=256)
    payload: dict[str, Any]


def normalize_webhook(provider: str, body: str, delivery_id: str) -> WebhookEvent:
    """Convert provider JSON into a stable event envelope.

    The normalizer is deliberately conservative: it preserves the relevant
    provider object under a namespaced key instead of guessing at fields that
    may change across API versions. Unknown event shapes remain observable as
    ``event.received`` rather than being silently discarded.
    """
    try:
        document = json.loads(body)
    except json.JSONDecodeError as exc:
        raise WebhookPayloadError("Webhook body is not valid JSON") from exc
    if not isinstance(document, dict):
        raise WebhookPayloadError("Webhook body must be a JSON object")

    normalized_provider = provider.strip().lower()
    if normalized_provider == "telegram":
        return _normalize_telegram(document, delivery_id)
    if normalized_provider == "meta":
        return _normalize_meta(document, delivery_id)
    return WebhookEvent(
        provider=normalized_provider,
        event_type="event.received",
        event_id=delivery_id,
        payload={"provider_payload": document},
    )


def _normalize_telegram(document: dict[str, Any], delivery_id: str) -> WebhookEvent:
    update_id = document.get("update_id")
    if isinstance(update_id, bool) or not isinstance(update_id, int):
        raise WebhookPayloadError("Telegram webhook is missing integer update_id")
    if isinstance(document.get("message"), dict):
        event_type = "message.received"
        source = document["message"]
    elif isinstance(document.get("callback_query"), dict):
        event_type = "callback.received"
        source = document["callback_query"]
    else:
        event_type = "update.received"
        source = document
    return WebhookEvent(
        provider="telegram",
        event_type=event_type,
        event_id=f"telegram:{update_id}",
        payload={"update_id": update_id, "update": source, "delivery_id": delivery_id},
    )


def _normalize_meta(document: dict[str, Any], delivery_id: str) -> WebhookEvent:
    object_name = document.get("object")
    entries = document.get("entry")
    first_entry = entries[0] if isinstance(entries, list) and entries else None
    if not isinstance(first_entry, dict):
        return WebhookEvent(
            provider="meta",
            event_type="event.received",
            event_id=delivery_id,
            payload={"object": object_name, "provider_payload": document, "delivery_id": delivery_id},
        )

    if object_name == "whatsapp_business_account":
        changes = first_entry.get("changes")
        first_change = changes[0] if isinstance(changes, list) and changes else None
        if isinstance(first_change, dict):
            value = first_change.get("value")
            if isinstance(value, dict):
                messages = value.get("messages")
                if isinstance(messages, list) and messages and isinstance(messages[0], dict):
                    message = messages[0]
                    event_id = message.get("id") if isinstance(message.get("id"), str) else delivery_id
                    return WebhookEvent(
                        provider="meta",
                        event_type="message.received",
                        event_id=event_id,
                        payload={"object": object_name, "change": first_change, "message": message},
                    )
                statuses = value.get("statuses")
                if isinstance(statuses, list) and statuses and isinstance(statuses[0], dict):
                    status = statuses[0]
                    event_id = status.get("id") if isinstance(status.get("id"), str) else delivery_id
                    return WebhookEvent(
                        provider="meta",
                        event_type="message.status",
                        event_id=event_id,
                        payload={"object": object_name, "change": first_change, "status": status},
                    )
            return WebhookEvent(
                provider="meta",
                event_type="change.received",
                event_id=delivery_id,
                payload={"object": object_name, "change": first_change},
            )

    messaging = first_entry.get("messaging")
    if isinstance(messaging, list) and messaging and isinstance(messaging[0], dict):
        message = messaging[0]
        event_id = message.get("message", {}).get("mid") if isinstance(message.get("message"), dict) else None
        return WebhookEvent(
            provider="meta",
            event_type="message.received" if isinstance(message.get("message"), dict) else "event.received",
            event_id=event_id if isinstance(event_id, str) else delivery_id,
            payload={"object": object_name, "entry": first_entry, "messaging": message},
        )
    return WebhookEvent(
        provider="meta",
        event_type="event.received",
        event_id=delivery_id,
        payload={"object": object_name, "entry": first_entry, "provider_payload": document},
    )
