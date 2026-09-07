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


def test_provider_specific_meta_events_preserve_whatsapp_and_instagram_identity():
    body = '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"id":"wamid.2"}]}}]}]}'
    whatsapp = normalize_webhook("whatsapp", body, "whatsapp:delivery")
    instagram = normalize_webhook(
        "instagram",
        '{"object":"instagram","entry":[{"messaging":[{"message":{"mid":"ig-mid-1"}}]}]}',
        "instagram:delivery",
    )
    assert whatsapp.provider == "whatsapp"
    assert whatsapp.event_id == "wamid.2"
    assert instagram.provider == "instagram"
    assert instagram.event_id == "ig-mid-1"


def test_zoom_meeting_event_is_normalized_to_provider_event_type():
    event = normalize_webhook(
        "zoom",
        '{"event":"meeting.started","payload":{"object":{"id":"meeting-1"}}}',
        "zoom:delivery",
    )
    assert event.event_type == "meeting.started"
    assert event.event_id == "meeting-1"
    assert event.payload["delivery_id"] == "zoom:delivery"


def test_slack_event_callback_is_normalized_to_inner_event():
    event = normalize_webhook(
        "slack",
        '{"type":"event_callback","event_id":"Ev-1","team_id":"T1","event":{"type":"message","text":"hi"}}',
        "slack:delivery",
    )
    assert event.event_type == "message"
    assert event.event_id == "Ev-1"
    assert event.payload["event"]["text"] == "hi"


def test_shopify_and_stripe_events_use_provider_metadata_and_ids():
    shopify = normalize_webhook(
        "shopify",
        '{"id":123,"name":"order"}',
        "shopify:delivery",
        {
            "topic": "orders/updated",
            "shop_domain": "example.myshopify.com",
            "event_id": "shopify-event-1",
        },
    )
    stripe = normalize_webhook(
        "stripe",
        '{"id":"evt_1","type":"payment_intent.succeeded","data":{"object":{}}}',
        "stripe:delivery",
    )
    assert shopify.event_type == "orders/updated"
    assert shopify.event_id == "shopify-event-1"
    assert shopify.payload["shop_domain"] == "example.myshopify.com"
    assert stripe.event_type == "payment_intent.succeeded"
    assert stripe.event_id == "evt_1"


@pytest.mark.parametrize("body", ["not-json", "[]", '{"message":{}}'])
def test_normalizer_rejects_invalid_telegram_shapes(body):
    with pytest.raises(WebhookPayloadError):
        normalize_webhook("telegram", body, "telegram:delivery")
