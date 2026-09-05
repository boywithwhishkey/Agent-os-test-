from __future__ import annotations

import hmac

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.integrations.webhooks import delivery_id, verify_meta_signature, verify_telegram_secret

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.get("/meta", include_in_schema=False)
async def meta_webhook_verification(request: Request) -> PlainTextResponse:
    """Meta/WhatsApp/Instagram webhook verification handshake."""
    if not settings.meta_webhook_verify_token:
        raise HTTPException(status_code=503, detail="META_WEBHOOK_VERIFY_TOKEN is not configured")
    query = request.query_params
    if query.get("hub.mode") != "subscribe" or not hmac_compare(
        query.get("hub.verify_token"), settings.meta_webhook_verify_token
    ):
        raise HTTPException(status_code=403, detail="Invalid Meta webhook verification")
    challenge = query.get("hub.challenge")
    if not challenge:
        raise HTTPException(status_code=400, detail="Meta webhook challenge is required")
    return PlainTextResponse(challenge)


@router.post("/meta")
async def meta_webhook(request: Request) -> dict[str, str | bool]:
    body = await request.body()
    if not settings.meta_app_secret:
        raise HTTPException(status_code=503, detail="META_APP_SECRET is not configured")
    if not verify_meta_signature(body, request.headers.get("x-hub-signature-256"), settings.meta_app_secret):
        raise HTTPException(status_code=403, detail="Invalid Meta webhook signature")
    return {"accepted": True, "provider": "meta", "delivery_id": delivery_id("meta", body)}


@router.post("/telegram")
async def telegram_webhook(request: Request) -> dict[str, str | bool]:
    body = await request.body()
    if not settings.telegram_webhook_secret_token:
        raise HTTPException(status_code=503, detail="TELEGRAM_WEBHOOK_SECRET_TOKEN is not configured")
    if not verify_telegram_secret(
        request.headers.get("x-telegram-bot-api-secret-token"), settings.telegram_webhook_secret_token
    ):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    return {"accepted": True, "provider": "telegram", "delivery_id": delivery_id("telegram", body)}


def hmac_compare(received: str | None, expected: str) -> bool:
    if not received:
        return False
    return hmac.compare_digest(received, expected)
