"""Request-scoped tenant context for credential-backed integrations.

The tenant is selected by authenticated server-side credentials, never by a
client-supplied tenant header.  OAuth callbacks are the one public route that
must establish the context without an API key; the signed, single-use OAuth
state record supplies that tenant after validation.
"""

from __future__ import annotations

from contextvars import ContextVar

current_tenant_id: ContextVar[str | None] = ContextVar(
    "current_tenant_id", default=None
)


def set_current_tenant(tenant_id: str) -> None:
    tenant = tenant_id.strip()
    if not tenant:
        raise ValueError("tenant id must be non-empty")
    current_tenant_id.set(tenant)


def get_current_tenant(fallback: str) -> str:
    return current_tenant_id.get() or fallback
