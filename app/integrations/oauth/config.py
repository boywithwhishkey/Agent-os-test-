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
        # Message history is split by conversation type in Slack. Request the
        # relevant read scopes up front; the adapter still accepts only a
        # bounded channel/cursor and fixed conversations.history method.
        scope=(
            "chat:write channels:read groups:read im:read mpim:read "
            "channels:history groups:history im:history mpim:history"
        ),
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
        scope=(
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/gmail.compose"
        ),
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "google_calendar": OAuthProviderConfig(
        id="google_calendar",
        name="Google Calendar",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://www.googleapis.com/auth/calendar.events",
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "google_drive": OAuthProviderConfig(
        id="google_drive",
        name="Google Drive",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope=(
            "https://www.googleapis.com/auth/drive.readonly "
            "https://www.googleapis.com/auth/drive.file"
        ),
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "google_sheets": OAuthProviderConfig(
        id="google_sheets",
        name="Google Sheets",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="openid email profile https://www.googleapis.com/auth/spreadsheets",
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    "linkedin": OAuthProviderConfig(
        id="linkedin",
        name="LinkedIn",
        authorize_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        scope="openid profile email w_member_social",
        client_id_env="LINKEDIN_OAUTH_CLIENT_ID",
        client_secret_env="LINKEDIN_OAUTH_CLIENT_SECRET",
    ),
    "pinterest": OAuthProviderConfig(
        id="pinterest",
        name="Pinterest",
        authorize_url="https://www.pinterest.com/oauth/",
        token_url="https://api.pinterest.com/v5/oauth/token",
        scope="user_accounts:read boards:read boards:write pins:read pins:write",
        client_id_env="PINTEREST_OAUTH_CLIENT_ID",
        client_secret_env="PINTEREST_OAUTH_CLIENT_SECRET",
        token_auth="basic",
    ),
    "jira": OAuthProviderConfig(
        id="jira",
        name="Jira",
        authorize_url="https://auth.atlassian.com/authorize",
        token_url="https://auth.atlassian.com/oauth/token",
        scope="read:jira-work write:jira-work offline_access",
        client_id_env="JIRA_OAUTH_CLIENT_ID",
        client_secret_env="JIRA_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"audience": "api.atlassian.com", "prompt": "consent"},
    ),
    "dropbox": OAuthProviderConfig(
        id="dropbox",
        name="Dropbox",
        authorize_url="https://www.dropbox.com/oauth2/authorize",
        token_url="https://api.dropboxapi.com/oauth2/token",
        scope="account_info.read files.metadata.read files.content.read files.content.write",
        client_id_env="DROPBOX_OAUTH_CLIENT_ID",
        client_secret_env="DROPBOX_OAUTH_CLIENT_SECRET",
        extra_authorize_params={"token_access_type": "offline"},
    ),
    "onedrive": OAuthProviderConfig(
        id="onedrive",
        name="OneDrive",
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scope="User.Read Files.ReadWrite offline_access",
        client_id_env="MICROSOFT_OAUTH_CLIENT_ID",
        client_secret_env="MICROSOFT_OAUTH_CLIENT_SECRET",
    ),
    "outlook": OAuthProviderConfig(
        id="outlook",
        name="Microsoft Outlook",
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scope="User.Read Mail.Read Mail.ReadWrite Mail.Send Calendars.ReadWrite offline_access",
        client_id_env="MICROSOFT_OAUTH_CLIENT_ID",
        client_secret_env="MICROSOFT_OAUTH_CLIENT_SECRET",
    ),
    "zoom": OAuthProviderConfig(
        id="zoom",
        name="Zoom",
        authorize_url="https://zoom.us/oauth/authorize",
        token_url="https://zoom.us/oauth/token",
        scope="user:read meeting:read meeting:write offline_access",
        client_id_env="ZOOM_OAUTH_CLIENT_ID",
        client_secret_env="ZOOM_OAUTH_CLIENT_SECRET",
        token_auth="basic",
    ),
    "snapchat": OAuthProviderConfig(
        id="snapchat",
        name="Snapchat",
        authorize_url="https://accounts.snapchat.com/login/oauth2/authorize",
        token_url="https://accounts.snapchat.com/login/oauth2/access_token",
        scope="snapchat-marketing-api snapchat-profile-api",
        client_id_env="SNAPCHAT_OAUTH_CLIENT_ID",
        client_secret_env="SNAPCHAT_OAUTH_CLIENT_SECRET",
    ),
    "whatsapp": OAuthProviderConfig(
        id="whatsapp",
        name="WhatsApp Cloud",
        authorize_url="https://www.facebook.com/v23.0/dialog/oauth",
        token_url="https://graph.facebook.com/v23.0/oauth/access_token",
        scope="whatsapp_business_management whatsapp_business_messaging",
        client_id_env="META_OAUTH_CLIENT_ID",
        client_secret_env="META_OAUTH_CLIENT_SECRET",
    ),
    "instagram": OAuthProviderConfig(
        id="instagram",
        name="Instagram",
        authorize_url="https://www.facebook.com/v23.0/dialog/oauth",
        token_url="https://graph.facebook.com/v23.0/oauth/access_token",
        scope=(
            "pages_show_list instagram_basic instagram_content_publish "
            "pages_read_engagement instagram_manage_comments"
        ),
        client_id_env="META_OAUTH_CLIENT_ID",
        client_secret_env="META_OAUTH_CLIENT_SECRET",
    ),
    "hubspot": OAuthProviderConfig(
        id="hubspot",
        name="HubSpot",
        authorize_url="https://app.hubspot.com/oauth/authorize",
        token_url="https://api.hubapi.com/oauth/v3/token",
        scope=(
            "oauth account-info.basic.read crm.objects.contacts.read "
            "crm.objects.contacts.write crm.objects.deals.read "
            "crm.objects.tickets.read"
        ),
        client_id_env="HUBSPOT_OAUTH_CLIENT_ID",
        client_secret_env="HUBSPOT_OAUTH_CLIENT_SECRET",
    ),
    "salesforce": OAuthProviderConfig(
        id="salesforce",
        name="Salesforce",
        authorize_url="https://login.salesforce.com/services/oauth2/authorize",
        token_url="https://login.salesforce.com/services/oauth2/token",
        scope="api refresh_token",
        client_id_env="SALESFORCE_OAUTH_CLIENT_ID",
        client_secret_env="SALESFORCE_OAUTH_CLIENT_SECRET",
    ),
}


def get_oauth_provider(provider_id: str) -> OAuthProviderConfig | None:
    return OAUTH_PROVIDERS.get(provider_id.lower().strip())
