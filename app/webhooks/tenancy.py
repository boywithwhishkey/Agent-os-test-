"""Tenant routing for verified provider webhook deliveries.

Webhook callbacks are anonymous by design, so they cannot use the normal
``X-API-Key`` tenant selector. They are authenticated by the provider's
signature/secret first, then routed using a server-held provider/account map.
No request header can select a tenant.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


class WebhookTenantNotConfigured(ValueError):
    """Raised when a verified delivery has no unambiguous tenant route."""


def resolve_webhook_tenant(
    provider: str,
    *,
    identifiers: Iterable[str] = (),
    routes: Mapping[str, str],
    default_tenant: str,
) -> str:
    """Resolve a verified delivery to one server-configured tenant.

    With no map configured, the legacy single-operator deployment tenant is
    retained. Once a map is present, an account-specific or provider fallback
    route must match and conflicting routes fail closed.
    """
    normalized_provider = provider.strip().lower()
    if not normalized_provider:
        raise WebhookTenantNotConfigured("Webhook provider is missing")
    candidates: list[str] = []
    seen: set[str] = set()
    for identifier in identifiers:
        if not isinstance(identifier, str):
            continue
        normalized_identifier = identifier.strip().lower()
        if not normalized_identifier or len(normalized_identifier) > 256:
            continue
        key = f"{normalized_provider}:{normalized_identifier}"
        if key not in seen:
            candidates.append(key)
            seen.add(key)
    if normalized_provider not in seen:
        candidates.append(normalized_provider)

    if not routes:
        tenant = default_tenant.strip()
        if not tenant:
            raise WebhookTenantNotConfigured("Webhook deployment tenant is empty")
        return tenant

    # An account-specific route is more precise than a provider fallback. A
    # fallback must not make an otherwise unambiguous account route appear
    # conflicting; multiple matching account routes still fail closed.
    specific_candidates = candidates[:-1]
    matching_candidates = specific_candidates or candidates[-1:]
    specific_matches = [routes[key] for key in matching_candidates if key in routes]
    matches = specific_matches if specific_matches else [routes[key] for key in candidates[-1:] if key in routes]
    unique_matches = {tenant.strip() for tenant in matches if tenant.strip()}
    if len(unique_matches) > 1:
        raise WebhookTenantNotConfigured(
            f"Webhook tenant routing is ambiguous for provider {normalized_provider}"
        )
    if not unique_matches:
        raise WebhookTenantNotConfigured(
            f"No webhook tenant route is configured for provider {normalized_provider}"
        )
    return unique_matches.pop()


def payload_identifiers(
    provider: str,
    document: Mapping[str, Any] | None,
    metadata: Mapping[str, Any] | None = None,
) -> list[str]:
    """Extract stable provider account identifiers, never secrets or payload text."""
    if not isinstance(document, Mapping):
        document = {}
    metadata = metadata if isinstance(metadata, Mapping) else {}
    normalized_provider = provider.strip().lower()
    identifiers: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip() and len(value.strip()) <= 256:
            normalized = value.strip()
            if normalized.lower() not in {item.lower() for item in identifiers}:
                identifiers.append(normalized)

    # Explicit metadata is used for Shopify headers and can also be supplied
    # by future verified provider routes.
    add(metadata.get("account_id"))
    add(metadata.get("shop_domain"))
    add(metadata.get("team_id"))
    add(metadata.get("event_account_id"))

    if normalized_provider == "stripe":
        add(document.get("account"))
        add(document.get("context"))
    elif normalized_provider == "slack":
        add(document.get("team_id"))
    elif normalized_provider == "zoom":
        add(document.get("account_id"))
    elif normalized_provider == "telegram":
        # Telegram normally has no bot id in an update. A bot_id, when a
        # provider proxy includes it, is safe to use; otherwise deployments
        # should configure the provider fallback route.
        add(document.get("bot_id"))
    elif normalized_provider in {"meta", "whatsapp", "instagram"}:
        add(document.get("object"))
        entries = document.get("entry")
        if isinstance(entries, list):
            for entry in entries[:32]:
                if not isinstance(entry, Mapping):
                    continue
                add(entry.get("id"))
                changes = entry.get("changes")
                if not isinstance(changes, list):
                    continue
                for change in changes[:32]:
                    if not isinstance(change, Mapping):
                        continue
                    value = change.get("value")
                    if not isinstance(value, Mapping):
                        continue
                    meta = value.get("metadata")
                    if isinstance(meta, Mapping):
                        add(meta.get("phone_number_id"))
                    add(value.get("phone_number_id"))
    return identifiers
