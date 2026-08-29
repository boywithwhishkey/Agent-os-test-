from __future__ import annotations

from app.core.config import settings
from app.integrations.base import IntegrationAdapter
from app.integrations.models import IntegrationProvider

_PROVIDER_META: dict[IntegrationProvider, dict[str, object]] = {
    IntegrationProvider.N8N: {
        "name": "n8n",
        "requires": ["N8N_BASE_URL"],
    },
    IntegrationProvider.GEMINI: {
        "name": "Google Gemini",
        "requires": ["GEMINI_API_KEY"],
    },
    IntegrationProvider.POSTGRESQL: {
        "name": "PostgreSQL",
        "requires": ["DATABASE_URL"],
    },
    IntegrationProvider.REDIS: {
        "name": "Redis",
        "requires": ["REDIS_URL"],
    },
    IntegrationProvider.OPENAI: {
        "name": "OpenAI",
        "requires": ["OPENAI_API_KEY"],
    },
    IntegrationProvider.ANTHROPIC: {
        "name": "Anthropic",
        "requires": ["ANTHROPIC_API_KEY"],
    },
    IntegrationProvider.CLOUDFLARE: {
        "name": "Cloudflare",
        "requires": ["CLOUDFLARE_API_TOKEN"],
    },
    IntegrationProvider.RENDER: {
        "name": "Render",
        "requires": ["RENDER_API_KEY"],
    },
    IntegrationProvider.GITHUB: {
        "name": "GitHub",
        "requires": ["GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_CLIENT_SECRET"],
    },
}


def build_integration_adapter(provider: str) -> IntegrationAdapter:
    normalized = provider.lower().strip()

    if normalized == "n8n":
        from app.integrations.n8n import N8NWebhookAdapter

        return N8NWebhookAdapter()
    if normalized == "gemini":
        from app.integrations.gemini import GeminiAdapter

        return GeminiAdapter()
    if normalized == "postgresql":
        from app.integrations.postgresql import PostgresAdapter

        return PostgresAdapter()
    if normalized == "redis":
        from app.integrations.redis import RedisAdapter

        return RedisAdapter()
    if normalized == "openai":
        from app.integrations.openai import OpenAIAdapter

        return OpenAIAdapter()
    if normalized == "anthropic":
        from app.integrations.anthropic import AnthropicAdapter

        return AnthropicAdapter()
    if normalized == "cloudflare":
        from app.integrations.cloudflare import CloudflareAdapter

        return CloudflareAdapter()
    if normalized == "render":
        from app.integrations.render import RenderAdapter

        return RenderAdapter()
    if normalized == "github":
        from app.integrations.github import GitHubOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return GitHubOAuthAdapter(connection_store=oauth_connection_store)

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
    if provider == IntegrationProvider.GEMINI:
        return bool(settings.gemini_api_key)
    if provider == IntegrationProvider.POSTGRESQL:
        return bool(settings.database_url.strip())
    if provider == IntegrationProvider.REDIS:
        return bool(settings.redis_url.strip())
    if provider == IntegrationProvider.OPENAI:
        return bool(settings.openai_api_key)
    if provider == IntegrationProvider.ANTHROPIC:
        return bool(settings.anthropic_api_key)
    if provider == IntegrationProvider.CLOUDFLARE:
        return bool(settings.cloudflare_api_token)
    if provider == IntegrationProvider.RENDER:
        return bool(settings.render_api_key)
    if provider == IntegrationProvider.GITHUB:
        return bool(settings.github_oauth_client_id) and bool(settings.github_oauth_client_secret)
    return False
