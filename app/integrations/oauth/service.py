from __future__ import annotations

import base64
from collections.abc import Awaitable, Callable
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.integrations.oauth.models import OAuthProviderConfig
from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore


class OAuthNotConfigured(RuntimeError):
    pass


class OAuthExchangeError(RuntimeError):
    pass


async def refresh_access_token(
    config: OAuthProviderConfig,
    *,
    connection_store: OAuthConnectionStore,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Refresh one stored OAuth connection without exposing credentials.

    Providers may rotate the refresh token, so the returned token pair is
    persisted atomically through the same encrypted store used by the initial
    code exchange. Callers should retry their original request once with the
    returned access token.
    """
    record = connection_store.get(config.id)
    if not record.refresh_token:
        raise OAuthExchangeError(f"{config.name} has no refresh token; authorize again")
    cid = client_id(config)
    secret = client_secret(config)
    if not cid or not secret:
        raise OAuthNotConfigured(f"{config.client_id_env} and {config.client_secret_env} are required")

    headers = {"Accept": "application/json"}
    payload = {"grant_type": "refresh_token", "refresh_token": record.refresh_token}
    request_kwargs: dict[str, object]
    if config.token_auth == "basic":
        credentials = base64.b64encode(f"{cid}:{secret}".encode()).decode()
        headers["Authorization"] = f"Basic {credentials}"
    else:
        payload["client_id"] = cid
        payload["client_secret"] = secret
    if config.token_body_format == "json":
        headers["Content-Type"] = "application/json"
        request_kwargs = {"json": payload}
    else:
        request_kwargs = {"data": payload}

    own_client = client is None
    http_client = client or httpx.AsyncClient()
    try:
        response = await http_client.post(config.token_url, headers=headers, timeout=15.0, **request_kwargs)
        try:
            body = response.json()
        except ValueError as exc:
            raise OAuthExchangeError(f"{config.name} returned a non-JSON refresh response") from exc
        if response.status_code >= 400 or "error" in body:
            message = body.get("error_description") or body.get("error") or f"HTTP {response.status_code}"
            connection_store.record_failure(config.id, error=str(message))
            await connection_store.persist(config.id)
            raise OAuthExchangeError(f"{config.name} rejected the refresh token: {message}")
        access_token = body.get("access_token")
        if not access_token:
            connection_store.record_failure(config.id, error="No access_token in refresh response")
            await connection_store.persist(config.id)
            raise OAuthExchangeError(f"{config.name} did not return an access token during refresh")
        connection_store.record_success(
            config.id,
            access_token=access_token,
            token_type=body.get("token_type") or record.token_type,
            scope=body.get("scope") or record.scope,
            refresh_token=body.get("refresh_token") or record.refresh_token,
            expires_in=body.get("expires_in"),
        )
        await connection_store.persist(config.id)
        return access_token
    except httpx.HTTPError as exc:
        connection_store.record_failure(config.id, error=f"{type(exc).__name__}: {exc}")
        await connection_store.persist(config.id)
        raise OAuthExchangeError(f"Could not reach {config.name} token refresh endpoint") from exc
    finally:
        if own_client:
            await http_client.aclose()


async def request_with_oauth_refresh(
    config: OAuthProviderConfig,
    *,
    connection_store: OAuthConnectionStore,
    client: httpx.AsyncClient,
    send: Callable[[str], Awaitable[httpx.Response]],
) -> httpx.Response:
    """Send once, refresh on a 401 when possible, and retry exactly once."""
    record = connection_store.get(config.id)
    if not record.access_token:
        raise OAuthExchangeError(f"Not authorized yet — connect a {config.name} account")
    response = await send(record.access_token)
    if response.status_code != 401 or not record.refresh_token:
        return response
    try:
        access_token = await refresh_access_token(config, connection_store=connection_store, client=client)
    except (OAuthExchangeError, OAuthNotConfigured):
        return response
    return await send(access_token)


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
        "state": state,
        "response_type": "code",
    }
    if config.scope:
        params["scope"] = config.scope
    params.update(config.extra_authorize_params)
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
        headers = {"Accept": "application/json"}
        payload = {"code": code, "redirect_uri": redirect_uri(config)}
        request_kwargs: dict[str, object]

        if config.token_auth == "basic":
            credentials = base64.b64encode(f"{client_id(config)}:{secret}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
            payload["grant_type"] = "authorization_code"
        else:
            payload["client_id"] = client_id(config)
            payload["client_secret"] = secret

        if config.token_body_format == "json":
            headers["Content-Type"] = "application/json"
            request_kwargs = {"json": payload}
        else:
            request_kwargs = {"data": payload}

        response = await http_client.post(
            config.token_url,
            headers=headers,
            timeout=15.0,
            **request_kwargs,
        )
        try:
            body = response.json()
        except ValueError as exc:
            raise OAuthExchangeError(f"{config.name} returned a non-JSON response") from exc

        if response.status_code >= 400 or "error" in body:
            message = body.get("error_description") or body.get("error") or f"HTTP {response.status_code}"
            connection_store.record_failure(config.id, error=str(message))
            await connection_store.persist(config.id)
            raise OAuthExchangeError(f"{config.name} rejected the authorization code: {message}")

        access_token = body.get("access_token")
        if not access_token:
            connection_store.record_failure(config.id, error="No access_token in response")
            await connection_store.persist(config.id)
            raise OAuthExchangeError(f"{config.name} did not return an access token")

        # Providers often omit refresh_token on a subsequent authorization.
        # Keep the previously rotated credential instead of silently making a
        # durable connection unable to refresh after the next access expiry.
        refresh_token = body.get("refresh_token") or connection_store.get(config.id).refresh_token
        connection_store.record_success(
            config.id,
            access_token=access_token,
            token_type=body.get("token_type"),
            scope=body.get("scope"),
            refresh_token=refresh_token,
            expires_in=body.get("expires_in"),
        )
        await connection_store.persist(config.id)
    except httpx.HTTPError as exc:
        connection_store.record_failure(config.id, error=f"{type(exc).__name__}: {exc}")
        await connection_store.persist(config.id)
        raise OAuthExchangeError(f"Could not reach {config.name}: {exc}") from exc
    finally:
        if own_client:
            await http_client.aclose()
