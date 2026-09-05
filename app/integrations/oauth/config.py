from __future__ import annotations

from app.integrations.oauth.models import OAuthProviderConfig

# Every OAuth2 catalog entry follows the same authorization-code flow. The
# providers below have Settings fields and real identity adapters; remaining
# providers are added only with the same complete config/adapter/test loop.
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
    "slack": OAuthProviderConfig(
        id="slack",
        name="Slack",
        authorize_url="https://slack.com/oauth/v2/authorize",
        token_url="https://slack.com/api/oauth.v2.access",
        scope="chat:write channels:read",
        client_id_env="SLACK_OAUTH_CLIENT_ID",
        client_secret_env="SLACK_OAUTH_CLIENT_SECRET",
        # Slack always answers 200, even on failure — it reports errors as
        # {"ok": false, "error": "..."} in the body, which the generic
        # `"error" in body` check in exchange_code() already handles.
    ),
    "notion": OAuthProviderConfig(
        id="notion",
        name="Notion",
        authorize_url="https://api.notion.com/v1/oauth/authorize",
        token_url="https://api.notion.com/v1/oauth/token",
        scope="",  # Notion has no OAuth scope param — capabilities are chosen when the integration is created
        client_id_env="NOTION_OAUTH_CLIENT_ID",
        client_secret_env="NOTION_OAUTH_CLIENT_SECRET",
        token_auth="basic",
        token_body_format="json",
        extra_authorize_params={"owner": "user"},
    ),
    "gitlab": OAuthProviderConfig(
        id="gitlab",
        name="GitLab",
        authorize_url="https://gitlab.com/oauth/authorize",
        token_url="https://gitlab.com/oauth/token",
        scope="read_api read_user",
        client_id_env="GITLAB_OAUTH_CLIENT_ID",
        client_secret_env="GITLAB_OAUTH_CLIENT_SECRET",
    ),
    "gmail": OAuthProviderConfig(
        id="gmail",
        name="Gmail",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://www.googleapis.com/auth/gmail.readonly",
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "google_calendar": OAuthProviderConfig(
        id="google_calendar",
        name="Google Calendar",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://www.googleapis.com/auth/calendar.readonly",
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "google_drive": OAuthProviderConfig(
        id="google_drive",
        name="Google Drive",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://www.googleapis.com/auth/drive.readonly",
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "jira": OAuthProviderConfig(
        id="jira",
        name="Jira",
        authorize_url="https://auth.atlassian.com/authorize",
        token_url="https://auth.atlassian.com/oauth/token",
        scope="read:jira-work offline_access",
        client_id_env="JIRA_OAUTH_CLIENT_ID",
        client_secret_env="JIRA_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"audience": "api.atlassian.com", "prompt": "consent"},
    ),
    "dropbox": OAuthProviderConfig(
        id="dropbox",
        name="Dropbox",
        authorize_url="https://www.dropbox.com/oauth2/authorize",
        token_url="https://api.dropboxapi.com/oauth2/token",
        scope="account_info.read files.metadata.read",
        client_id_env="DROPBOX_OAUTH_CLIENT_ID",
        client_secret_env="DROPBOX_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"token_access_type": "offline"},
    ),
    "onedrive": OAuthProviderConfig(
        id="onedrive",
        name="OneDrive",
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scope="User.Read Files.Read offline_access",
        client_id_env="MICROSOFT_OAUTH_CLIENT_ID",
        client_secret_env="MICROSOFT_OAUTH_CLIENT_SECRET",
    ),
}


def get_oauth_provider(provider_id: str) -> OAuthProviderConfig | None:
    return OAUTH_PROVIDERS.get(provider_id.lower().strip())
