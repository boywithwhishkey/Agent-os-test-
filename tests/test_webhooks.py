from __future__ import annotations

import hashlib
import hmac

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


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
