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
    IntegrationProvider.SLACK: {
        "name": "Slack",
        "requires": ["SLACK_OAUTH_CLIENT_ID", "SLACK_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.NOTION: {
        "name": "Notion",
        "requires": ["NOTION_OAUTH_CLIENT_ID", "NOTION_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.GITLAB: {
        "name": "GitLab",
        "requires": ["GITLAB_OAUTH_CLIENT_ID", "GITLAB_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.MAKE: {
        "name": "Make",
        "requires": ["MAKE_WEBHOOK_URL"],
    },
    IntegrationProvider.DISCORD: {
        "name": "Discord",
        "requires": ["DISCORD_WEBHOOK_URL"],
    },
    IntegrationProvider.TELEGRAM: {
        "name": "Telegram",
        "requires": ["TELEGRAM_BOT_TOKEN"],
    },
    IntegrationProvider.WHATSAPP: {
        "name": "WhatsApp Cloud",
        "requires": ["META_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
    },
    IntegrationProvider.INSTAGRAM: {
        "name": "Instagram",
        "requires": ["META_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"],
    },
    IntegrationProvider.TEAMS: {
        "name": "Microsoft Teams",
        "requires": ["TEAMS_WEBHOOK_URL"],
    },
    IntegrationProvider.SHOPIFY: {
        "name": "Shopify",
        "requires": ["SHOPIFY_ADMIN_ACCESS_TOKEN", "SHOPIFY_SHOP_DOMAIN"],
    },
    IntegrationProvider.STRIPE: {
        "name": "Stripe",
        "requires": ["STRIPE_SECRET_KEY"],
    },
    IntegrationProvider.SNAPCHAT: {
        "name": "Snapchat",
        "requires": ["SNAPCHAT_ACCESS_TOKEN"],
    },
    IntegrationProvider.WOOCOMMERCE: {
        "name": "WooCommerce",
        "requires": [
            "WOOCOMMERCE_STORE_URL",
            "WOOCOMMERCE_CONSUMER_KEY",
            "WOOCOMMERCE_CONSUMER_SECRET",
        ],
    },
    IntegrationProvider.VERCEL: {
        "name": "Vercel",
        "requires": ["VERCEL_API_TOKEN"],
    },
    IntegrationProvider.LINEAR: {
        "name": "Linear",
        "requires": ["LINEAR_API_KEY"],
    },
    IntegrationProvider.AMAZON: {
        "name": "Amazon Selling Partner API",
        "requires": [
            "AMAZON_LWA_CLIENT_ID",
            "AMAZON_LWA_CLIENT_SECRET",
            "AMAZON_LWA_REFRESH_TOKEN",
            "AMAZON_AWS_ACCESS_KEY_ID",
            "AMAZON_AWS_SECRET_ACCESS_KEY",
        ],
    },
    IntegrationProvider.GMAIL: {
        "name": "Gmail",
        "requires": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.GOOGLE_CALENDAR: {
        "name": "Google Calendar",
        "requires": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.GOOGLE_DRIVE: {
        "name": "Google Drive",
        "requires": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.JIRA: {
        "name": "Jira",
        "requires": [
            "JIRA_OAUTH_CLIENT_ID",
            "JIRA_OAUTH_CLIENT_SECRET",
            "JIRA_CLOUD_ID",
        ],
    },
    IntegrationProvider.DROPBOX: {
        "name": "Dropbox",
        "requires": ["DROPBOX_OAUTH_CLIENT_ID", "DROPBOX_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.ONEDRIVE: {
        "name": "OneDrive",
        "requires": ["MICROSOFT_OAUTH_CLIENT_ID", "MICROSOFT_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.HUBSPOT: {
        "name": "HubSpot",
        "requires": ["HUBSPOT_OAUTH_CLIENT_ID", "HUBSPOT_OAUTH_CLIENT_SECRET"],
    },
    IntegrationProvider.SALESFORCE: {
        "name": "Salesforce",
        "requires": [
            "SALESFORCE_OAUTH_CLIENT_ID",
            "SALESFORCE_OAUTH_CLIENT_SECRET",
            "SALESFORCE_INSTANCE_URL",
        ],
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
    if normalized == "slack":
        from app.integrations.oauth.registry import oauth_connection_store
        from app.integrations.slack import SlackOAuthAdapter

        return SlackOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "notion":
        from app.integrations.notion import NotionOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return NotionOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "gitlab":
        from app.integrations.gitlab import GitLabOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return GitLabOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "make":
        from app.integrations.make import MakeWebhookAdapter

        return MakeWebhookAdapter()
    if normalized == "discord":
        from app.integrations.discord import DiscordWebhookAdapter

        return DiscordWebhookAdapter()
    if normalized == "telegram":
        from app.integrations.telegram import TelegramBotAdapter

        return TelegramBotAdapter()
    if normalized == "whatsapp":
        from app.integrations.whatsapp import WhatsAppCloudAdapter

        return WhatsAppCloudAdapter()
    if normalized == "instagram":
        from app.integrations.instagram import InstagramGraphAdapter

        return InstagramGraphAdapter()
    if normalized == "teams":
        from app.integrations.teams import TeamsWebhookAdapter

        return TeamsWebhookAdapter()
    if normalized == "shopify":
        from app.integrations.shopify import ShopifyAdminAdapter

        return ShopifyAdminAdapter()
    if normalized == "stripe":
        from app.integrations.stripe import StripeAdapter

        return StripeAdapter()
    if normalized == "snapchat":
        from app.integrations.snapchat import SnapchatMarketingAdapter

        return SnapchatMarketingAdapter()
    if normalized == "woocommerce":
        from app.integrations.woocommerce import WooCommerceAdapter

        return WooCommerceAdapter()
    if normalized == "vercel":
        from app.integrations.vercel import VercelAdapter

        return VercelAdapter()
    if normalized == "linear":
        from app.integrations.linear import LinearAdapter

        return LinearAdapter()
    if normalized == "amazon":
        from app.integrations.amazon import AmazonSPAPIAdapter

        return AmazonSPAPIAdapter()
    if normalized in {"gmail", "google_calendar", "google_drive"}:
        from app.integrations.google import GoogleOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return GoogleOAuthAdapter(
            provider=IntegrationProvider(normalized), connection_store=oauth_connection_store
        )
    if normalized == "jira":
        from app.integrations.jira import JiraOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return JiraOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "dropbox":
        from app.integrations.dropbox import DropboxOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return DropboxOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "onedrive":
        from app.integrations.oauth.registry import oauth_connection_store
        from app.integrations.onedrive import OneDriveOAuthAdapter

        return OneDriveOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "hubspot":
        from app.integrations.hubspot import HubSpotOAuthAdapter
        from app.integrations.oauth.registry import oauth_connection_store

        return HubSpotOAuthAdapter(connection_store=oauth_connection_store)
    if normalized == "salesforce":
        from app.integrations.oauth.registry import oauth_connection_store
        from app.integrations.salesforce import SalesforceOAuthAdapter

        return SalesforceOAuthAdapter(connection_store=oauth_connection_store)

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
    if provider == IntegrationProvider.SLACK:
        return bool(settings.slack_oauth_client_id) and bool(settings.slack_oauth_client_secret)
    if provider == IntegrationProvider.NOTION:
        return bool(settings.notion_oauth_client_id) and bool(settings.notion_oauth_client_secret)
    if provider == IntegrationProvider.GITLAB:
        return bool(settings.gitlab_oauth_client_id) and bool(settings.gitlab_oauth_client_secret)
    if provider == IntegrationProvider.MAKE:
        return bool(settings.make_webhook_url)
    if provider == IntegrationProvider.DISCORD:
        return bool(settings.discord_webhook_url)
    if provider == IntegrationProvider.TELEGRAM:
        return bool(settings.telegram_bot_token)
    if provider == IntegrationProvider.WHATSAPP:
        return bool(settings.meta_access_token and settings.whatsapp_phone_number_id)
    if provider == IntegrationProvider.INSTAGRAM:
        return bool(settings.meta_access_token and settings.instagram_business_account_id)
    if provider == IntegrationProvider.TEAMS:
        return bool(settings.teams_webhook_url)
    if provider == IntegrationProvider.SHOPIFY:
        return bool(settings.shopify_admin_access_token and settings.shopify_shop_domain)
    if provider == IntegrationProvider.STRIPE:
        return bool(settings.stripe_secret_key)
    if provider == IntegrationProvider.SNAPCHAT:
        return bool(settings.snapchat_access_token)
    if provider == IntegrationProvider.WOOCOMMERCE:
        return bool(
            settings.woocommerce_store_url
            and settings.woocommerce_consumer_key
            and settings.woocommerce_consumer_secret
        )
    if provider == IntegrationProvider.VERCEL:
        return bool(settings.vercel_api_token)
    if provider == IntegrationProvider.LINEAR:
        return bool(settings.linear_api_key)
    if provider == IntegrationProvider.AMAZON:
        return bool(
            settings.amazon_lwa_client_id
            and settings.amazon_lwa_client_secret
            and settings.amazon_lwa_refresh_token
            and settings.amazon_aws_access_key_id
            and settings.amazon_aws_secret_access_key
        )
    if provider in {
        IntegrationProvider.GMAIL,
        IntegrationProvider.GOOGLE_CALENDAR,
        IntegrationProvider.GOOGLE_DRIVE,
    }:
        return bool(settings.google_oauth_client_id and settings.google_oauth_client_secret)
    if provider == IntegrationProvider.JIRA:
        return bool(
            settings.jira_oauth_client_id
            and settings.jira_oauth_client_secret
            and settings.jira_cloud_id
        )
    if provider == IntegrationProvider.DROPBOX:
        return bool(settings.dropbox_oauth_client_id and settings.dropbox_oauth_client_secret)
    if provider == IntegrationProvider.ONEDRIVE:
        return bool(settings.microsoft_oauth_client_id and settings.microsoft_oauth_client_secret)
    if provider == IntegrationProvider.HUBSPOT:
        return bool(settings.hubspot_oauth_client_id and settings.hubspot_oauth_client_secret)
    if provider == IntegrationProvider.SALESFORCE:
        return bool(
            settings.salesforce_oauth_client_id
            and settings.salesforce_oauth_client_secret
            and settings.salesforce_instance_url
        )
    return False
