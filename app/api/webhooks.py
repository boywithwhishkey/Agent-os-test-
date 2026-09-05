from __future__ import annotations

import hmac

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.integrations.webhooks import delivery_id, verify_meta_signature, verify_telegram_secret
from app.queue.base import JobQueue, QueueJob
from app.queue.factory import build_job_queue

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
_delivery_queue: JobQueue | None = None


def _get_delivery_queue() -> JobQueue:
    global _delivery_queue
    if _delivery_queue is None:
        _delivery_queue = build_job_queue()
    return _delivery_queue


async def _accept_delivery(provider: str, body: bytes) -> dict[str, str | bool]:
    if len(body) > settings.webhook_max_body_bytes:
        raise HTTPException(status_code=413, detail="Webhook payload is too large")
    try:
        raw_body = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Webhook payload must be UTF-8") from exc
    identifier = delivery_id(provider, body)
    queue = _get_delivery_queue()
    if not await queue.claim_once(identifier):
        return {"accepted": True, "duplicate": True, "provider": provider, "delivery_id": identifier}
    await queue.enqueue(
        QueueJob(
            queue="webhooks",
            type="connector.webhook",
            payload={"provider": provider, "body": raw_body, "delivery_id": identifier},
        )
    )
    return {"accepted": True, "duplicate": False, "provider": provider, "delivery_id": identifier}


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
    return await _accept_delivery("meta", body)


@router.post("/telegram")
async def telegram_webhook(request: Request) -> dict[str, str | bool]:
    body = await request.body()
    if not settings.telegram_webhook_secret_token:
        raise HTTPException(status_code=503, detail="TELEGRAM_WEBHOOK_SECRET_TOKEN is not configured")
    if not verify_telegram_secret(
        request.headers.get("x-telegram-bot-api-secret-token"), settings.telegram_webhook_secret_token
    ):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    return await _accept_delivery("telegram", body)


def hmac_compare(received: str | None, expected: str) -> bool:
    if not received:
        return False
    return hmac.compare_digest(received, expected)
