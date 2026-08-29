from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class OAuthProviderConfig:
    """Static OAuth2 metadata for one provider. Registering a new provider
    here — plus a CLIENT_ID/CLIENT_SECRET pair in Settings — is the entire
    integration surface; the authorize/callback routes and state handling
    below are fully generic.

    Most providers (GitHub, Slack, GitLab) accept client_id/client_secret
    as form fields in the token exchange body — that's `token_auth="body"`.
    Notion instead requires HTTP Basic auth with a JSON body
    (`token_auth="basic"`, `token_body_format="json"`) — see
    app/integrations/oauth/service.py's exchange_code().
    """

    id: str
    name: str
    authorize_url: str
    token_url: str
    scope: str
    client_id_env: str
    client_secret_env: str
    token_auth: str = "body"  # "body" | "basic"
    token_body_format: str = "form"  # "form" | "json"
    extra_authorize_params: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class OAuthStateRecord:
    provider: str
    created_at: datetime


@dataclass(slots=True)
class OAuthConnectionRecord:
    provider: str
    access_token: str | None = None
    token_type: str | None = None
    scope: str | None = None
    connected_at: str | None = None
    last_error: str | None = None

    @property
    def connected(self) -> bool:
        return self.access_token is not None

    def to_public(self) -> OAuthConnectionPublic:
        return OAuthConnectionPublic(
            provider=self.provider,
            connected=self.connected,
            token_type=self.token_type,
            scope=self.scope,
            connected_at=self.connected_at,
            last_error=self.last_error,
        )


class OAuthConnectionPublic(BaseModel):
    """Redacted view of an OAuth connection — the access token is never
    serialized to any API response."""

    provider: str
    connected: bool
    token_type: str | None = None
    scope: str | None = None
    connected_at: str | None = None
    last_error: str | None = None


class OAuthAuthorizeResponse(BaseModel):
    authorize_url: str


def utcnow() -> datetime:
    return datetime.now(UTC)
