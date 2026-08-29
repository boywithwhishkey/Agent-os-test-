from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.integrations.oauth.models import OAuthProviderConfig
from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore


class OAuthNotConfigured(RuntimeError):
    pass


class OAuthExchangeError(RuntimeError):
    pass


def _credential(env_name: str) -> str | None:
    # Every OAuth Settings field is named exactly its env var lowercased —
    # see app/core/config.py (github_oauth_client_id / GITHUB_OAUTH_CLIENT_ID).
    return getattr(settings, env_name.lower(), None)


def client_id(config: OAuthProviderConfig) -> str | None:
    return _credential(config.client_id_env)


def client_secret(config: OAuthProviderConfig) -> str | None:
    return _credential(config.client_secret_env)


def is_configured(config: OAuthProviderConfig) -> bool:
    return bool(client_id(config)) and bool(client_secret(config))


def redirect_uri(config: OAuthProviderConfig) -> str:
    base = settings.oauth_redirect_base_url.rstrip("/")
    return f"{base}/api/v1/integrations/oauth/{config.id}/callback"


def build_authorize_url(config: OAuthProviderConfig, state_store: OAuthStateStore) -> str:
    cid = client_id(config)
    if not cid:
        raise OAuthNotConfigured(f"{config.client_id_env} is required")

    state = state_store.create(config.id)
    params = {
        "client_id": cid,
        "redirect_uri": redirect_uri(config),
        "scope": config.scope,
        "state": state,
        "response_type": "code",
    }
    return f"{config.authorize_url}?{urlencode(params)}"


async def exchange_code(
    config: OAuthProviderConfig,
    *,
    code: str,
    connection_store: OAuthConnectionStore,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Exchange an authorization code for an access token and record the
    result. Raises OAuthExchangeError on any failure; callers decide how to
    surface that (this module never leaks the client secret or raw token in
    an exception message)."""
    secret = client_secret(config)
    if not secret:
        raise OAuthNotConfigured(f"{config.client_secret_env} is required")

    own_client = client is None
    http_client = client or httpx.AsyncClient()
    try:
        response = await http_client.post(
            config.token_url,
            data={
                "client_id": client_id(config),
                "client_secret": secret,
                "code": code,
                "redirect_uri": redirect_uri(config),
            },
            headers={"Accept": "application/json"},
            timeout=15.0,
        )
        try:
            body = response.json()
        except ValueError as exc:
            raise OAuthExchangeError(f"{config.name} returned a non-JSON response") from exc

        if response.status_code >= 400 or "error" in body:
            message = body.get("error_description") or body.get("error") or f"HTTP {response.status_code}"
            connection_store.record_failure(config.id, error=str(message))
            raise OAuthExchangeError(f"{config.name} rejected the authorization code: {message}")

        access_token = body.get("access_token")
        if not access_token:
            connection_store.record_failure(config.id, error="No access_token in response")
            raise OAuthExchangeError(f"{config.name} did not return an access token")

        connection_store.record_success(
            config.id,
            access_token=access_token,
            token_type=body.get("token_type"),
            scope=body.get("scope"),
        )
    except httpx.HTTPError as exc:
        connection_store.record_failure(config.id, error=f"{type(exc).__name__}: {exc}")
        raise OAuthExchangeError(f"Could not reach {config.name}: {exc}") from exc
    finally:
        if own_client:
            await http_client.aclose()
