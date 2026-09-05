from __future__ import annotations

import pytest

from app.webhooks.events import WebhookPayloadError, normalize_webhook


def test_telegram_message_is_normalized_to_canonical_event():
    event = normalize_webhook(
        "telegram",
        '{"update_id": 42, "message": {"message_id": 7, "text": "hello"}}',
        "telegram:delivery",
    )
    assert event.event_type == "message.received"
    assert event.event_id == "telegram:42"
    assert event.payload["update"]["text"] == "hello"


def test_meta_whatsapp_message_and_status_are_normalized():
    message = normalize_webhook(
        "meta",
        '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"id":"wamid.1","text":{"body":"hi"}}]}}]}]}',
        "meta:delivery",
    )
    status = normalize_webhook(
        "meta",
        '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"statuses":[{"id":"wamid.1","status":"delivered"}]}}]}]}',
        "meta:delivery-2",
    )
    assert message.event_type == "message.received"
    assert message.event_id == "wamid.1"
    assert status.event_type == "message.status"
    assert status.payload["status"]["status"] == "delivered"


@pytest.mark.parametrize("body", ["not-json", "[]", '{"message":{}}'])
def test_normalizer_rejects_invalid_telegram_shapes(body):
    with pytest.raises(WebhookPayloadError):
        normalize_webhook("telegram", body, "telegram:delivery")
