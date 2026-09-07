"""Operator authentication for protected API routes.

Status-code contract, deliberately explicit because these three cases were
previously conflated:

    401 Unauthorized      the caller sent no credential, or a wrong one.
                          Retrying WITH a valid credential will succeed.
    403 Forbidden         the caller is authenticated but lacks permission.
                          Not reachable today: API keys select isolated
                          tenants but do not carry roles or scopes, so there
                          is no "authenticated but not allowed" state to be in.
                          The response shape supports it so that adding a
                          permission model later does not require re-designing
                          the error contract.
    503 Service Unavail.  the SERVER has no API key configured, so no
                          credential can ever authenticate. This is a
                          deployment gap, not a client error — answering 401
                          here would tell the caller to go and find a
                          credential that cannot exist.

That last distinction is the one that mattered in practice: the frontend
treated 401 and 503 identically and told operators to "Sign in" when the
server itself was misconfigured, sending them to fix the one thing that could
not help.
"""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, Request

from app.core.config import settings
from app.core.tenant import set_current_tenant

# RFC 7235 requires a challenge on every 401. The scheme is an extension token
# (the credential travels in X-API-Key, not Authorization), which §2.1 permits.
# It names the realm and nothing else: a challenge that reported whether a key
# was recognised would be an oracle.
_CHALLENGE = {"WWW-Authenticate": 'ApiKey realm="THYNACT"'}


def _unauthorized(code: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        # `detail` is kept as the human string the client already renders;
        # `code` is added for programmatic branching so clients never have to
        # match on prose.
        detail={"detail": "Unauthorized", "code": code},
        headers=_CHALLENGE,
    )


async def require_api_key(
    request: Request, x_api_key: str | None = Header(default=None)
) -> None:
    configured_keys = settings.api_key_tenants
    if not configured_keys:
        raise HTTPException(
            status_code=503,
            detail={
                "detail": "API authentication is not configured",
                "code": "auth_not_configured",
            },
        )
    if not x_api_key:
        raise _unauthorized("authentication_required")
    # Constant-time: a plain != leaks how many leading characters matched
    # through response timing, which over many requests recovers the key.
    matched_tenant: str | None = None
    for configured_key, tenant_id in configured_keys.items():
        # Compare every configured key so response timing does not reveal
        # which tenant key matched.
        if secrets.compare_digest(x_api_key, configured_key):
            matched_tenant = tenant_id
    if matched_tenant is None:
        raise _unauthorized("authentication_invalid")
    set_current_tenant(matched_tenant)
    request.state.tenant_id = matched_tenant


async def optional_api_key_tenant(
    x_api_key: str | None = Header(default=None),
) -> None:
    """Apply a valid API-key tenant to an otherwise public read route.

    Anonymous catalog reads remain backward compatible and use the deployment
    tenant. Invalid optional credentials are ignored here; state-changing and
    protected routes still use ``require_api_key`` and return 401.
    """
    if not x_api_key:
        return
    for configured_key, tenant_id in settings.api_key_tenants.items():
        if secrets.compare_digest(x_api_key, configured_key):
            set_current_tenant(tenant_id)
            return
