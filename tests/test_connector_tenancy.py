"""Characterisation tests for how connector credentials are actually scoped.

CLAUDE.md states a multi-tenancy invariant — credentials are per-tenant, and a
user-owned external account must never be served by a global fallback
credential. Today the code does not implement it: every `OAuthConnectionStore`
implementation is keyed by provider alone, with no tenant or principal
anywhere in the interface, so there is exactly one GitHub connection per
deployment — whichever backend stores it.

That is not currently a violation, because THYNACT has no user accounts: a
deployment is one operator behind one API key, so "per deployment" and "per
operator" are the same set. It becomes a violation the moment a second
principal exists, and the failure mode is silent — everyone's requests would
transparently use whoever authorised last.

These tests pin the real contract so that transition cannot happen by
accident. They are written to FAIL when tenancy is introduced, which is the
point: whoever adds it has to come here and state the new scoping deliberately.

Pinned on the ABSTRACT `OAuthConnectionStore` interface, not one concrete
implementation, because the guarantee that matters is that NEITHER
`InMemoryOAuthConnectionStore` NOR `PostgresOAuthConnectionStore` can accept a
tenant/principal — a persistent backend is exactly where scope-creep like a
quietly-added `tenant_id` column would first show up.
"""

from __future__ import annotations

import inspect

import pytest

from app.integrations.oauth.store import InMemoryOAuthConnectionStore, OAuthConnectionStore

pytestmark = pytest.mark.asyncio


async def test_the_interface_itself_has_no_tenant_or_principal_parameter() -> None:
    # Checked on the ABC: a future implementation inherits this signature and
    # cannot narrow it, so this is the one place that actually forecloses the
    # possibility for every backend at once.
    signature = inspect.signature(OAuthConnectionStore.record_success)
    assert "tenant" not in signature.parameters
    assert "principal" not in signature.parameters
    assert set(signature.parameters) == {"self", "provider", "access_token", "token_type", "scope"}


async def test_oauth_connections_are_scoped_to_the_deployment_not_a_principal() -> None:
    store = InMemoryOAuthConnectionStore()
    await store.record_success("github", access_token="token-a", token_type="bearer", scope="repo")

    # Consequence, stated explicitly: a second authorisation replaces the
    # first for everyone, rather than sitting beside it.
    await store.record_success("github", access_token="token-b", token_type="bearer", scope="repo")
    record = await store.get("github")
    assert record.access_token == "token-b"


async def test_disconnect_removes_the_connection_for_the_whole_deployment() -> None:
    store = InMemoryOAuthConnectionStore()
    await store.record_success("slack", access_token="t", token_type="bearer", scope=None)
    assert await store.disconnect("slack") is True
    # Not "disconnected for me" — gone.
    record = await store.get("slack")
    assert record.access_token is None


async def test_access_tokens_never_leave_the_process_in_a_public_view() -> None:
    """The one part of the credential contract that IS enforced today."""
    store = InMemoryOAuthConnectionStore()
    await store.record_success("notion", access_token="secret-token-value", token_type="bearer", scope="read")
    record = await store.get("notion")
    public = record.to_public()
    assert "secret-token-value" not in public.model_dump_json()
    assert not hasattr(public, "access_token")
