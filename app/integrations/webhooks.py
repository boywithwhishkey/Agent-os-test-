from __future__ import annotations

import hashlib
import hmac


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


def delivery_id(provider: str, body: bytes) -> str:
    """Return a non-sensitive deterministic id for queue/deduplication layers."""
    digest = hashlib.sha256(body).hexdigest()[:24]
    return f"{provider}:{digest}"
