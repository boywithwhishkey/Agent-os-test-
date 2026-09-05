from __future__ import annotations

import time
from collections.abc import Callable

import httpx

from app.integrations.oauth.store import OAuthConnectionStore

InterpretFn = Callable[[httpx.Response], tuple[bool, str | None]]


class OAuthNotConnected(RuntimeError):
    """No user has completed Authorize for this connector yet.

    Raised by `oauth_get`, not returned as a value, so it takes the same path
    as any other adapter failure through the broker — but the broker's
    `_configured` check (see broker.py's `_oauth_connected`) is meant to catch
    this before an adapter is ever invoked. Reaching here is a bug in that
    check, not the ordinary "please connect your account" case.
    """


async def oauth_get(
    *,
    provider_id: str,
    provider_name: str,
    url: str,
    connection_store: OAuthConnectionStore,
    build_headers: Callable[[str], dict[str, str]],
    client: httpx.AsyncClient | None = None,
) -> dict:
    """One authenticated, read-only GET against a connected OAuth provider.

    The shared shape behind every OAuth adapter's `run_capability`: look up the
    stored token, make one GET, raise on anything other than 200 rather than
    returning a partial or misleading body. Adapters differ only in the URL and
    headers, exactly as they already do in `verify_oauth_identity`.
    """
    record = connection_store.get(provider_id)
    if not record.access_token:
        raise OAuthNotConnected(f"No {provider_name} account connected")

    own_client = client is None
    http_client = client or httpx.AsyncClient()
    try:
        response = await http_client.get(url, headers=build_headers(record.access_token), timeout=10.0)
        response.raise_for_status()
        return response.json()
    finally:
        if own_client:
            await http_client.aclose()


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
        response = await http_client.get(identity_url, headers=build_headers(record.access_token), timeout=10.0)
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
