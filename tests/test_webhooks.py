from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

import app.api.webhooks as webhook_routes
from app.core.config import settings
from app.main import app
from app.queue.base import InMemoryJobQueue


def test_meta_verification_requires_secret_and_returns_challenge(monkeypatch):
    monkeypatch.setattr(settings, "meta_webhook_verify_token", "verify-me")
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/webhooks/meta",
            params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "123"},
        )
    assert response.status_code == 200
    assert response.text == "123"


def test_meta_webhook_accepts_only_valid_hmac(monkeypatch):
    monkeypatch.setattr(settings, "meta_app_secret", "app-secret")
    monkeypatch.setattr(webhook_routes, "_delivery_queue", InMemoryJobQueue())
    body = b'{"object":"whatsapp_business_account"}'
    signature = hmac.new(b"app-secret", body, hashlib.sha256).hexdigest()
    with TestClient(app) as client:
        accepted = client.post(
            "/api/v1/webhooks/meta", content=body, headers={"X-Hub-Signature-256": f"sha256={signature}"}
        )
        rejected = client.post(
            "/api/v1/webhooks/meta", content=body, headers={"X-Hub-Signature-256": "sha256=" + "0" * 64}
        )
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True
    assert rejected.status_code == 403


def test_valid_webhook_is_queued_and_duplicate_is_suppressed(monkeypatch):
    monkeypatch.setattr(settings, "meta_app_secret", "app-secret")
    queue = InMemoryJobQueue()
    monkeypatch.setattr(webhook_routes, "_delivery_queue", queue)
    body = b'{"object":"whatsapp_business_account"}'
    signature = hmac.new(b"app-secret", body, hashlib.sha256).hexdigest()
    headers = {"X-Hub-Signature-256": f"sha256={signature}"}

    with TestClient(app) as client:
        first = client.post("/api/v1/webhooks/meta", content=body, headers=headers)
        second = client.post("/api/v1/webhooks/meta", content=body, headers=headers)

    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True


def test_telegram_webhook_requires_secret_header(monkeypatch):
    monkeypatch.setattr(settings, "telegram_webhook_secret_token", "telegram-secret")
    with TestClient(app) as client:
        accepted = client.post(
            "/api/v1/webhooks/telegram",
            content=b'{"update_id":1}',
            headers={"X-Telegram-Bot-Api-Secret-Token": "telegram-secret"},
        )
        rejected = client.post(
            "/api/v1/webhooks/telegram",
            content=b'{"update_id":1}',
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        )
    assert accepted.status_code == 200
    assert accepted.json()["provider"] == "telegram"
    assert rejected.status_code == 403


def _slack_headers(body: bytes, secret: str, timestamp: str | None = None) -> dict[str, str]:
    timestamp = timestamp or str(int(time.time()))
    digest = hmac.new(secret.encode(), f"v0:{timestamp}:".encode() + body, hashlib.sha256).hexdigest()
    return {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": f"v0={digest}",
    }


def test_slack_webhook_answers_url_verification_challenge(monkeypatch):
    secret = "slack-signing-secret"
    monkeypatch.setattr(settings, "slack_signing_secret", secret)
    body = json.dumps({"type": "url_verification", "challenge": "challenge-1"}).encode()

    with TestClient(app) as client:
        response = client.post("/api/v1/webhooks/slack", content=body, headers=_slack_headers(body, secret))

    assert response.status_code == 200
    assert response.json() == {"challenge": "challenge-1"}


def test_slack_webhook_queues_verified_event_and_rejects_replay(monkeypatch):
    secret = "slack-signing-secret"
    monkeypatch.setattr(settings, "slack_signing_secret", secret)
    queue = InMemoryJobQueue()
    monkeypatch.setattr(webhook_routes, "_delivery_queue", queue)
    body = b'{"type":"event_callback","event_id":"Ev-1","event":{"type":"message","text":"hi"}}'
    headers = _slack_headers(body, secret)

    with TestClient(app) as client:
        accepted = client.post("/api/v1/webhooks/slack", content=body, headers=headers)
        duplicate = client.post("/api/v1/webhooks/slack", content=body, headers=headers)
        rejected = client.post(
            "/api/v1/webhooks/slack",
            content=body,
            headers={**headers, "X-Slack-Signature": "v0=" + "0" * 64},
        )
        stale = client.post(
            "/api/v1/webhooks/slack",
            content=body,
            headers=_slack_headers(
                body,
                secret,
                timestamp=str(int(time.time()) - settings.slack_webhook_max_skew_seconds - 1),
            ),
        )

    assert accepted.status_code == 200
    assert accepted.json()["provider"] == "slack"
    assert duplicate.json()["duplicate"] is True
    assert rejected.status_code == 403
    assert stale.status_code == 403


def _zoom_headers(body: bytes, secret: str) -> dict[str, str]:
    timestamp = str(int(time.time()))
    message = f"v0:{timestamp}:{body.decode()}".encode()
    digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return {"X-Zm-Request-Timestamp": timestamp, "X-Zm-Signature": f"v0={digest}"}


def test_zoom_webhook_answers_validation_challenge(monkeypatch):
    secret = "zoom-secret"
    monkeypatch.setattr(settings, "zoom_webhook_secret_token", secret)
    body = json.dumps(
        {"event": "endpoint.url_validation", "payload": {"plainToken": "plain-token"}}
    ).encode()

    with TestClient(app) as client:
        response = client.post("/api/v1/webhooks/zoom", content=body, headers=_zoom_headers(body, secret))

    expected = hmac.new(secret.encode(), b"plain-token", hashlib.sha256).hexdigest()
    assert response.status_code == 200
    assert response.json() == {"plainToken": "plain-token", "encryptedToken": expected}


def test_zoom_webhook_queues_verified_event_and_rejects_replay(monkeypatch):
    secret = "zoom-secret"
    monkeypatch.setattr(settings, "zoom_webhook_secret_token", secret)
    queue = InMemoryJobQueue()
    monkeypatch.setattr(webhook_routes, "_delivery_queue", queue)
    body = b'{"event":"meeting.started","payload":{"object":{"id":"meeting-1"}}}'
    headers = _zoom_headers(body, secret)

    with TestClient(app) as client:
        accepted = client.post("/api/v1/webhooks/zoom", content=body, headers=headers)
        duplicate = client.post("/api/v1/webhooks/zoom", content=body, headers=headers)
        rejected = client.post(
            "/api/v1/webhooks/zoom",
            content=body,
            headers={**headers, "X-Zm-Signature": "v0=" + "0" * 64},
        )

    assert accepted.status_code == 200
    assert accepted.json()["provider"] == "zoom"
    assert duplicate.json()["duplicate"] is True
    assert rejected.status_code == 403


def _shopify_headers(body: bytes, secret: str, webhook_id: str = "shopify-delivery-1") -> dict[str, str]:
    digest = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    return {
        "X-Shopify-Hmac-Sha256": digest,
        "X-Shopify-Webhook-Id": webhook_id,
        "X-Shopify-Topic": "orders/updated",
        "X-Shopify-Shop-Domain": "example.myshopify.com",
        "X-Shopify-Event-Id": "shopify-event-1",
    }


def test_shopify_webhook_verifies_raw_body_and_deduplicates_by_delivery_id(monkeypatch):
    secret = "shopify-secret"
    monkeypatch.setattr(settings, "shopify_webhook_secret", secret)
    queue = InMemoryJobQueue()
    monkeypatch.setattr(webhook_routes, "_delivery_queue", queue)
    body = b'{"id":123,"name":"order"}'
    headers = _shopify_headers(body, secret)

    with TestClient(app) as client:
        accepted = client.post("/api/v1/webhooks/shopify", content=body, headers=headers)
        duplicate = client.post("/api/v1/webhooks/shopify", content=body, headers=headers)
        rejected = client.post(
            "/api/v1/webhooks/shopify",
            content=body,
            headers={**headers, "X-Shopify-Hmac-Sha256": "0" * len(headers["X-Shopify-Hmac-Sha256"])},
        )

    assert accepted.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert rejected.status_code == 403


def test_shopify_webhook_stamps_server_resolved_tenant_on_queue_job(monkeypatch):
    secret = "shopify-secret"
    monkeypatch.setattr(settings, "shopify_webhook_secret", secret)
    monkeypatch.setattr(
        settings,
        "webhook_tenant_map",
        '{"shopify:example.myshopify.com":"merchant-a"}',
    )
    queue = InMemoryJobQueue()
    monkeypatch.setattr(webhook_routes, "_delivery_queue", queue)
    body = b'{"id":123}'
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/webhooks/shopify",
            content=body,
            headers=_shopify_headers(body, secret),
        )
    assert response.status_code == 200
    job = __import__("asyncio").run(queue.dequeue("webhooks"))
    assert job is not None
    assert job.payload["tenant_id"] == "merchant-a"


def _stripe_headers(body: bytes, secret: str, timestamp: int | None = None) -> dict[str, str]:
    timestamp = timestamp or int(time.time())
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return {"Stripe-Signature": f"t={timestamp},v1={digest}"}


def test_stripe_webhook_verifies_signed_event_and_rejects_stale_delivery(monkeypatch):
    secret = "whsec_test"
    monkeypatch.setattr(settings, "stripe_webhook_secret", secret)
    queue = InMemoryJobQueue()
    monkeypatch.setattr(webhook_routes, "_delivery_queue", queue)
    body = b'{"id":"evt_1","type":"payment_intent.succeeded","data":{"object":{}}}'
    headers = _stripe_headers(body, secret)

    with TestClient(app) as client:
        accepted = client.post("/api/v1/webhooks/stripe", content=body, headers=headers)
        duplicate = client.post("/api/v1/webhooks/stripe", content=body, headers=headers)
        stale = client.post(
            "/api/v1/webhooks/stripe",
            content=body,
            headers=_stripe_headers(body, secret, int(time.time()) - settings.stripe_webhook_max_skew_seconds - 1),
        )

    assert accepted.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert stale.status_code == 403
