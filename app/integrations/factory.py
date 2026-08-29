from __future__ import annotations

from app.core.config import settings
from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationProvider
from app.integrations.n8n import N8NWebhookAdapter

_PROVIDER_META: dict[IntegrationProvider, dict[str, object]] = {
    IntegrationProvider.N8N: {
        "name": "n8n",
        "requires": ["N8N_BASE_URL"],
    },
}


def build_integration_adapter(provider: str) -> IntegrationAdapter:
    normalized = provider.lower().strip()
    if normalized == "n8n":
        return N8NWebhookAdapter()
    raise RuntimeError(f"Unsupported integration provider: {provider}")


def list_providers() -> list[IntegrationProvider]:
    return list(_PROVIDER_META.keys())


def provider_display_name(provider: IntegrationProvider) -> str:
    return str(_PROVIDER_META[provider]["name"])


def provider_requirements(provider: IntegrationProvider) -> list[str]:
    return list(_PROVIDER_META[provider]["requires"])  # type: ignore[arg-type]


def is_provider_configured(provider: IntegrationProvider) -> bool:
    if provider == IntegrationProvider.N8N:
        return bool(settings.n8n_base_url.strip())
    return False
