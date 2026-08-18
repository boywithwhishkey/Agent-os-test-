from __future__ import annotations

from app.integrations.base import IntegrationAdapter
from app.integrations.n8n import N8NWebhookAdapter


def build_integration_adapter(provider: str) -> IntegrationAdapter:
    normalized = provider.lower().strip()
    if normalized == "n8n":
        return N8NWebhookAdapter()
    raise RuntimeError(f"Unsupported integration provider: {provider}")
