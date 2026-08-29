from __future__ import annotations

from app.integrations.oauth.models import OAuthProviderConfig

# Every OAuth2 catalog entry follows the same authorization-code flow; only
# GitHub has real Settings fields wired up today (see app/core/config.py),
# so it is the only one marked implemented=True in the catalog. Adding the
# next provider (Slack, Notion, ...) is: add its config here, its
# CLIENT_ID/CLIENT_SECRET fields to Settings, and flip implemented=True on
# its CatalogSpec.
OAUTH_PROVIDERS: dict[str, OAuthProviderConfig] = {
    "github": OAuthProviderConfig(
        id="github",
        name="GitHub",
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        scope="repo read:org",
        client_id_env="GITHUB_OAUTH_CLIENT_ID",
        client_secret_env="GITHUB_OAUTH_CLIENT_SECRET",
    ),
}


def get_oauth_provider(provider_id: str) -> OAuthProviderConfig | None:
    return OAUTH_PROVIDERS.get(provider_id.lower().strip())
