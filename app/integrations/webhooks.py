from __future__ import annotations

import hashlib
import hmac
import time


def verify_meta_signature(body: bytes, signature_header: str | None, app_secret: str | None) -> bool:
    """Validate Meta's X-Hub-Signature-256 header without accepting a bodyless secret."""
    if not body or not signature_header or not app_secret:
        return False
    scheme, separator, supplied = signature_header.partition("=")
    if separator != "=" or scheme != "sha256" or len(supplied) != 64:
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)


def verify_telegram_secret(received: str | None, expected: str | None) -> bool:
    """Validate Telegram's secret-token header using constant-time comparison."""
    if not received or not expected:
        return False
    return hmac.compare_digest(received, expected)


def verify_slack_signature(
    body: bytes,
    timestamp: str | None,
    signature_header: str | None,
    signing_secret: str | None,
    *,
    max_skew_seconds: int = 300,
    now: float | None = None,
) -> bool:
    """Validate Slack's v0 signature and reject stale/replayed requests."""
    if not body or not timestamp or not signature_header or not signing_secret:
        return False
    if not timestamp.isdigit() or len(timestamp) > 12:
        return False
    if not signature_header.startswith("v0=") or len(signature_header) != 67:
        return False
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return False
    clock = time.time() if now is None else now
    if abs(clock - timestamp_value) > max_skew_seconds:
        return False
    try:
        body_text = body.decode("utf-8")
    except UnicodeDecodeError:
        return False
    message = f"v0:{timestamp}:{body_text}".encode()
    digest = hmac.new(signing_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, f"v0={digest}")


def verify_zoom_signature(
    body: bytes,
    timestamp: str | None,
    signature_header: str | None,
    secret_token: str | None,
    *,
    max_skew_seconds: int = 300,
    now: float | None = None,
) -> bool:
    """Verify Zoom's v0 HMAC signature and reject replayed timestamps."""
    if not body or not timestamp or not signature_header or not secret_token:
        return False
    if not timestamp.isdigit() or len(timestamp) > 12:
        return False
    if not signature_header.startswith("v0=") or len(signature_header) != 67:
        return False
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return False
    clock = time.time() if now is None else now
    if abs(clock - timestamp_value) > max_skew_seconds:
        return False
    try:
        body_text = body.decode("utf-8")
    except UnicodeDecodeError:
        return False
    message = f"v0:{timestamp}:{body_text}".encode()
    digest = hmac.new(secret_token.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header, f"v0={digest}")


def delivery_id(provider: str, body: bytes) -> str:
    """Return a non-sensitive deterministic id for queue/deduplication layers."""
    digest = hashlib.sha256(body).hexdigest()[:24]
    return f"{provider}:{digest}"
