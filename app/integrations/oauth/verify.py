from __future__ import annotations

import time
from collections.abc import Callable

import httpx

from app.integrations.oauth.config import get_oauth_provider
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore

InterpretFn = Callable[[httpx.Response], tuple[bool, str | None]]


def default_interpret(response: httpx.Response) -> tuple[bool, str | None]:
    if response.status_code == 200:
        return True, None
    if response.status_code == 401:
        return False, "The stored token was rejected (HTTP 401) — connect the account again"
    return False, f"HTTP {response.status_code}"


async def verify_oauth_identity(
    *,
    provider_id: str,
    provider_name: str,
    identity_url: str,
    connection_store: OAuthConnectionStore,
    build_headers: Callable[[str], dict[str, str]],
    interpret: InterpretFn = default_interpret,
    client: httpx.AsyncClient | None = None,
) -> tuple[bool, float | None, str | None]:
    """Shared "is the stored OAuth token still good?" probe used by every
    OAuth adapter's test_connection(): a single free, read-only identity
    call. Providers differ only in the identity endpoint, headers, and how
    a failure is reported (most use HTTP status; Slack always answers 200
    and reports failure in the JSON body — see `interpret`)."""
    record = connection_store.get(provider_id)
    if not record.access_token:
        return False, None, f"Not connected yet — use Connect to link a {provider_name} account."

    own_client = client is None
    http_client = client or httpx.AsyncClient()
    started = time.perf_counter()
    try:
        config = get_oauth_provider(provider_id)
        if config is None:
            response = await http_client.get(
                identity_url, headers=build_headers(record.access_token), timeout=10.0
            )
        else:
            response = await request_with_oauth_refresh(
                config,
                connection_store=connection_store,
                client=http_client,
                send=lambda token: http_client.get(
                    identity_url, headers=build_headers(token), timeout=10.0
                ),
            )
        latency_ms = (time.perf_counter() - started) * 1000
        ok, error = interpret(response)
        return ok, latency_ms, error
    except httpx.TimeoutException:
        return False, None, f"Connection to {provider_name} timed out"
    except httpx.HTTPError as exc:
        return False, None, f"{type(exc).__name__}: {exc}"
    finally:
        if own_client:
            await http_client.aclose()
