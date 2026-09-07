"""Regression tests for tenant-scoped connector credentials.

The API key is the tenant selector. There is deliberately no client-supplied
tenant header: a caller can only select a tenant for which the deployment
holds a server-side key mapping. OAuth state carries the same tenant across
the public callback, and connection records are keyed by ``(tenant, provider)``
in both memory and PostgreSQL-backed modes.
"""

from __future__ import annotations

import json
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api import phase9
from app.core.config import settings
from app.core.tenant import current_tenant_id
from app.integrations.oauth.registry import oauth_connection_store, oauth_state_store
from app.integrations.oauth.store import OAuthConnectionStore, OAuthStateStore
from app.main import app


@contextmanager
def tenant(tenant_id: str):
    token = current_tenant_id.set(tenant_id)
    try:
        yield
    finally:
        current_tenant_id.reset(token)


def test_oauth_connections_are_isolated_between_tenants() -> None:
    store = OAuthConnectionStore()

    with tenant("tenant-a"):
        store.record_success("github", access_token="token-a", token_type="bearer", scope="repo")
    with tenant("tenant-b"):
        store.record_success("github", access_token="token-b", token_type="bearer", scope="repo")

    with tenant("tenant-a"):
        assert store.get("github").access_token == "token-a"
        assert store.disconnect("github") is True
        assert store.get("github").access_token is None
    with tenant("tenant-b"):
        assert store.get("github").access_token == "token-b"


def test_api_connector_credentials_are_scoped_and_never_fall_back_cross_tenant(monkeypatch) -> None:
    monkeypatch.setattr(settings, "oauth_tenant_id", "operator")
    monkeypatch.setattr(
        settings,
        "connector_credentials_json",
        json.dumps({"tenant-a": {"STRIPE_SECRET_KEY": "sk_tenant_a"}}),
    )
    with tenant("tenant-a"):
        assert settings.connector_credential("STRIPE_SECRET_KEY", "sk_global") == "sk_tenant_a"
    with tenant("tenant-b"):
        assert settings.connector_credential("STRIPE_SECRET_KEY", "sk_global") is None
    with tenant("operator"):
        assert settings.connector_credential("STRIPE_SECRET_KEY", "sk_global") == "sk_global"


def test_scoped_stripe_adapter_uses_the_active_tenant_credential(monkeypatch) -> None:
    from app.integrations.stripe import StripeAdapter

    monkeypatch.setattr(settings, "oauth_tenant_id", "operator")
    monkeypatch.setattr(
        settings,
        "connector_credentials_json",
        json.dumps({"tenant-a": {"STRIPE_SECRET_KEY": "sk_tenant_a"}}),
    )
    with tenant("tenant-a"):
        adapter = StripeAdapter()
        assert adapter.secret_key == "sk_tenant_a"
    with tenant("tenant-b"):
        try:
            StripeAdapter()
        except RuntimeError as exc:
            assert "STRIPE_SECRET_KEY" in str(exc)
        else:  # pragma: no cover - defensive assertion
            raise AssertionError("tenant-b reused tenant-a's Stripe credential")


def test_oauth_state_claim_carries_the_owning_tenant() -> None:
    store = OAuthStateStore()
    with tenant("tenant-a"):
        state = store.create("slack")

    with tenant("operator"):
        claim = store.consume_claim(state)

    assert claim is not None
    assert claim.provider == "slack"
    assert claim.tenant_id == "tenant-a"


def test_access_tokens_never_leave_the_process_in_a_public_view() -> None:
    store = OAuthConnectionStore()
    with tenant("tenant-a"):
        store.record_success("notion", access_token="secret-token-value", token_type="bearer", scope="read")
        public = store.get("notion").to_public()
    assert "secret-token-value" not in public.model_dump_json()
    assert not hasattr(public, "access_token")


def test_server_held_api_keys_select_isolated_disconnect_target(monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_key", None)
    monkeypatch.setattr(
        settings,
        "api_keys_json",
        json.dumps({"key-a": "tenant-a", "key-b": "tenant-b"}),
    )
    monkeypatch.setattr(settings, "github_oauth_client_id", "client")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret")
    oauth_connection_store._connections.clear()
    with tenant("tenant-a"):
        oauth_connection_store.record_success("github", access_token="a", token_type="bearer", scope="repo")
    with tenant("tenant-b"):
        oauth_connection_store.record_success("github", access_token="b", token_type="bearer", scope="repo")

    with TestClient(app) as client:
        response = client.delete(
            "/api/v1/integrations/oauth/github", headers={"X-API-Key": "key-a"}
        )
    assert response.status_code == 204
    with tenant("tenant-a"):
        assert oauth_connection_store.get("github").connected is False
    with tenant("tenant-b"):
        assert oauth_connection_store.get("github").access_token == "b"


def test_public_oauth_callback_restores_state_tenant(monkeypatch) -> None:
    monkeypatch.setattr(settings, "github_oauth_client_id", "client")
    monkeypatch.setattr(settings, "github_oauth_client_secret", "secret")
    oauth_state_store._states.clear()
    oauth_connection_store._connections.clear()
    with tenant("tenant-a"):
        state = oauth_state_store.create("github")

    async def fake_exchange(config, *, code, connection_store, client=None):
        connection_store.record_success(
            config.id, access_token="tenant-a-token", token_type="bearer", scope="repo"
        )

    monkeypatch.setattr(phase9, "exchange_code", fake_exchange)
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/integrations/oauth/github/callback?state={state}&code=ok",
            follow_redirects=False,
        )
    assert response.status_code in (302, 307)
    with tenant("tenant-a"):
        assert oauth_connection_store.get("github").access_token == "tenant-a-token"
    with tenant("operator"):
        assert oauth_connection_store.get("github").connected is False
