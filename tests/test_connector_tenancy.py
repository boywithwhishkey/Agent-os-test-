"""Characterisation tests for how connector credentials are actually scoped.

CLAUDE.md states a multi-tenancy invariant — credentials are per-tenant, and a
user-owned external account must never be served by a global fallback
credential. Today the code does not implement it: `OAuthConnectionStore` is a
`dict[provider, record]` with no tenant or principal in the key, so there is
exactly one GitHub connection per deployment.

That is not currently a violation, because THYNACT has no user accounts: a
deployment is one operator behind one API key, so "per deployment" and "per
operator" are the same set. It becomes a violation the moment a second
principal exists, and the failure mode is silent — everyone's requests would
transparently use whoever authorised last.

These tests pin the real contract so that transition cannot happen by
accident. They are written to FAIL when tenancy is introduced, which is the
point: whoever adds it has to come here and state the new scoping deliberately.
"""

from __future__ import annotations

import inspect

from app.integrations.oauth.store import OAuthConnectionStore


def test_oauth_connections_are_scoped_to_the_deployment_not_a_principal() -> None:
    store = OAuthConnectionStore()
    store.record_success("github", access_token="token-a", token_type="bearer", scope="repo")

    # There is no principal argument to pass, and no way to ask for "my"
    # connection as opposed to "the" connection.
    signature = inspect.signature(store.record_success)
    assert "tenant" not in signature.parameters
    assert "principal" not in signature.parameters
    assert set(signature.parameters) == {
        "provider",
        "access_token",
        "token_type",
        "scope",
        "refresh_token",
    }

    # Consequence, stated explicitly: a second authorisation replaces the first
    # for everyone, rather than sitting beside it.
    store.record_success("github", access_token="token-b", token_type="bearer", scope="repo")
    assert store.get("github").access_token == "token-b"


def test_disconnect_removes_the_connection_for_the_whole_deployment() -> None:
    store = OAuthConnectionStore()
    store.record_success("slack", access_token="t", token_type="bearer", scope=None)
    assert store.disconnect("slack") is True
    # Not "disconnected for me" — gone.
    assert store.get("slack").access_token is None


def test_access_tokens_never_leave_the_process_in_a_public_view() -> None:
    """The one part of the credential contract that IS enforced today."""
    store = OAuthConnectionStore()
    store.record_success("notion", access_token="secret-token-value", token_type="bearer", scope="read")
    public = store.get("notion").to_public()
    assert "secret-token-value" not in public.model_dump_json()
    assert not hasattr(public, "access_token")
