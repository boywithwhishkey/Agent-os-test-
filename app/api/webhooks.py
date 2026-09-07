from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.integrations.webhooks import (
    delivery_id,
    verify_meta_signature,
    verify_shopify_signature,
    verify_slack_signature,
    verify_stripe_signature,
    verify_telegram_secret,
    verify_zoom_signature,
)
from app.queue.base import JobQueue, QueueJob
from app.queue.factory import build_job_queue
from app.webhooks.tenancy import (
    WebhookTenantNotConfigured,
    payload_identifiers,
    resolve_webhook_tenant,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
_delivery_queue: JobQueue | None = None


def _get_delivery_queue() -> JobQueue:
    global _delivery_queue
    if _delivery_queue is None:
        _delivery_queue = build_job_queue()
    return _delivery_queue


async def _accept_delivery(
    provider: str,
    body: bytes,
    *,
    delivery_key: str | None = None,
    metadata: dict[str, str] | None = None,
) -> dict[str, str | bool]:
    if len(body) > settings.webhook_max_body_bytes:
        raise HTTPException(status_code=413, detail="Webhook payload is too large")
    try:
        raw_body = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Webhook payload must be UTF-8") from exc
    try:
        document = json.loads(raw_body)
    except json.JSONDecodeError:
        document = None
    try:
        tenant_id = resolve_webhook_tenant(
            provider,
            identifiers=payload_identifiers(provider, document, metadata),
            routes=settings.webhook_tenant_routes,
            default_tenant=settings.oauth_tenant_id,
        )
    except WebhookTenantNotConfigured as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if delivery_key and 1 <= len(delivery_key) <= 256:
        identifier = f"{provider}:{delivery_key}"
    else:
        identifier = delivery_id(provider, body)
    queue = _get_delivery_queue()
    if not await queue.claim_once(identifier):
        return {"accepted": True, "duplicate": True, "provider": provider, "delivery_id": identifier}
    await queue.enqueue(
        QueueJob(
            queue="webhooks",
            type="connector.webhook",
            payload={
                "provider": provider,
                "body": raw_body,
                "delivery_id": identifier,
                "metadata": metadata or {},
                "tenant_id": tenant_id,
            },
        )
    )
    return {"accepted": True, "duplicate": False, "provider": provider, "delivery_id": identifier}


@router.get("/meta", include_in_schema=False)
async def meta_webhook_verification(request: Request) -> PlainTextResponse:
    """Legacy Meta/WhatsApp/Instagram webhook verification handshake."""
    return _meta_verification_response(request)


@router.get("/whatsapp", include_in_schema=False)
async def whatsapp_webhook_verification(request: Request) -> PlainTextResponse:
    """WhatsApp-specific Meta webhook verification handshake."""
    return _meta_verification_response(request)


@router.get("/instagram", include_in_schema=False)
async def instagram_webhook_verification(request: Request) -> PlainTextResponse:
    """Instagram-specific Meta webhook verification handshake."""
    return _meta_verification_response(request)


def _meta_verification_response(request: Request) -> PlainTextResponse:
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
    return await _accept_meta_webhook(request, provider="meta")


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request) -> dict[str, str | bool]:
    """Verify and queue a WhatsApp Cloud callback under its own provider id."""
    return await _accept_meta_webhook(request, provider="whatsapp")


@router.post("/instagram")
async def instagram_webhook(request: Request) -> dict[str, str | bool]:
    """Verify and queue an Instagram Graph callback under its own provider id."""
    return await _accept_meta_webhook(request, provider="instagram")


async def _accept_meta_webhook(
    request: Request, *, provider: str
) -> dict[str, str | bool]:
    body = await request.body()
    if not settings.meta_app_secret:
        raise HTTPException(status_code=503, detail="META_APP_SECRET is not configured")
    if not verify_meta_signature(body, request.headers.get("x-hub-signature-256"), settings.meta_app_secret):
        raise HTTPException(status_code=403, detail="Invalid Meta webhook signature")
    return await _accept_delivery(provider, body)


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


@router.post("/slack")
async def slack_webhook(request: Request) -> dict[str, str | bool]:
    """Verify and queue Slack Events API callbacks."""
    body = await request.body()
    secret = settings.slack_signing_secret
    if not secret:
        raise HTTPException(status_code=503, detail="SLACK_SIGNING_SECRET is not configured")
    if not verify_slack_signature(
        body,
        request.headers.get("x-slack-request-timestamp"),
        request.headers.get("x-slack-signature"),
        secret,
        max_skew_seconds=settings.slack_webhook_max_skew_seconds,
    ):
        raise HTTPException(status_code=403, detail="Invalid Slack webhook signature")
    try:
        document = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Slack webhook payload must be valid JSON") from exc
    if not isinstance(document, dict):
        raise HTTPException(status_code=400, detail="Slack webhook payload must be a JSON object")
    if document.get("type") == "url_verification":
        challenge = document.get("challenge")
        if not isinstance(challenge, str) or not 1 <= len(challenge) <= 512:
            raise HTTPException(status_code=400, detail="Slack webhook challenge is invalid")
        return {"challenge": challenge}
    return await _accept_delivery("slack", body)


@router.post("/zoom")
async def zoom_webhook(request: Request) -> dict[str, str | bool]:
    """Verify and queue Zoom events, answering Zoom's endpoint challenge."""
    body = await request.body()
    secret = settings.zoom_webhook_secret_token
    if not secret:
        raise HTTPException(status_code=503, detail="ZOOM_WEBHOOK_SECRET_TOKEN is not configured")
    if not verify_zoom_signature(
        body,
        request.headers.get("x-zm-request-timestamp"),
        request.headers.get("x-zm-signature"),
        secret,
        max_skew_seconds=settings.zoom_webhook_max_skew_seconds,
    ):
        raise HTTPException(status_code=403, detail="Invalid Zoom webhook signature")
    try:
        document = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Zoom webhook payload must be valid JSON") from exc
    if not isinstance(document, dict):
        raise HTTPException(status_code=400, detail="Zoom webhook payload must be a JSON object")
    if document.get("event") == "endpoint.url_validation":
        payload = document.get("payload")
        plain_token = payload.get("plainToken") if isinstance(payload, dict) else None
        if not isinstance(plain_token, str) or not 1 <= len(plain_token) <= 512:
            raise HTTPException(status_code=400, detail="Zoom webhook challenge is invalid")
        encrypted = hmac.new(secret.encode("utf-8"), plain_token.encode("utf-8"), hashlib.sha256).hexdigest()
        return {"plainToken": plain_token, "encryptedToken": encrypted}
    return await _accept_delivery("zoom", body)


@router.post("/shopify")
async def shopify_webhook(request: Request) -> dict[str, str | bool]:
    """Verify and queue Shopify HTTPS deliveries using raw-body HMAC."""
    body = await request.body()
    secret = settings.shopify_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="SHOPIFY_WEBHOOK_SECRET is not configured")
    if not verify_shopify_signature(body, request.headers.get("x-shopify-hmac-sha256"), secret):
        raise HTTPException(status_code=403, detail="Invalid Shopify webhook signature")
    metadata = {
        key: value
        for key, value in {
            "topic": request.headers.get("x-shopify-topic"),
            "shop_domain": request.headers.get("x-shopify-shop-domain"),
            "event_id": request.headers.get("x-shopify-event-id"),
        }.items()
        if value
    }
    return await _accept_delivery(
        "shopify",
        body,
        delivery_key=request.headers.get("x-shopify-webhook-id"),
        metadata=metadata,
    )


@router.post("/stripe")
async def stripe_webhook(request: Request) -> dict[str, str | bool]:
    """Verify and queue Stripe events using the raw-body signed payload."""
    body = await request.body()
    secret = settings.stripe_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET is not configured")
    if not verify_stripe_signature(
        body,
        request.headers.get("stripe-signature"),
        secret,
        max_skew_seconds=settings.stripe_webhook_max_skew_seconds,
    ):
        raise HTTPException(status_code=403, detail="Invalid Stripe webhook signature")
    return await _accept_delivery("stripe", body)


def hmac_compare(received: str | None, expected: str) -> bool:
    if not received:
        return False
    return hmac.compare_digest(received, expected)
