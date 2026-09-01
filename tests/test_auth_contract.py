"""HTTP status contract for operator authentication.

These lock down the distinction that was previously collapsed: a caller with no
credential (401) is a different situation from a server with no credential
configured (503), and answering the second with the first sent operators to
"sign in" when signing in could not possibly help.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

# Representative protected routes across different routers, so a regression in
# one router's dependency wiring is caught rather than assumed absent.
PROTECTED_ROUTES = [
    "/api/v1/tools",
    "/api/v1/tools/audit",
    "/api/v1/runtime/status",
]

# Deliberately anonymous: the integrations catalogue describes WHICH providers
# exist and whether each is configured, never any credential. Asserted below so
# that if it ever starts returning secrets, a test fails rather than a human
# having to notice.
PUBLIC_ROUTES = [
    "/api/v1/integrations",
    "/api/v1/integrations/mcp/servers",
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "unit-test-key")
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_missing_credentials_returns_401(client, route):
    response = client.get(route)

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Unauthorized"
    assert body["code"] == "authentication_required"


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_invalid_credentials_returns_401(client, route):
    response = client.get(route, headers={"X-API-Key": "not-the-key"})

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_invalid"


def test_401_carries_a_www_authenticate_challenge(client):
    """RFC 7235 §3.1 requires a challenge on 401."""
    response = client.get("/api/v1/tools")

    assert response.headers["www-authenticate"] == 'ApiKey realm="THYNACT"'


def test_401_challenge_does_not_reveal_whether_a_key_was_recognised(client):
    """The challenge must be byte-identical for both failure modes, so it
    cannot be used as an oracle for guessing valid keys."""
    missing = client.get("/api/v1/tools")
    invalid = client.get("/api/v1/tools", headers={"X-API-Key": "wrong"})

    assert missing.headers["www-authenticate"] == invalid.headers["www-authenticate"]
    assert missing.json()["detail"] == invalid.json()["detail"]


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_server_without_configured_key_returns_503_not_401(monkeypatch, route):
    """No credential can authenticate against a server that has none, so this
    is a service problem, not a client one. Answering 401 would tell the caller
    to supply a credential that cannot exist."""
    monkeypatch.setattr(settings, "api_key", None)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(route)

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "auth_not_configured"
    # A 503 is not an authentication challenge, so it must not carry one.
    assert "www-authenticate" not in {k.lower() for k in response.headers}


def test_valid_credentials_succeed(client):
    response = client.get("/api/v1/tools", headers={"X-API-Key": "unit-test-key"})

    assert response.status_code == 200


def test_plain_string_details_keep_the_original_body_shape(client):
    """The structured-error handler must not change the wire shape for the many
    routes that raise HTTPException with a plain string."""
    response = client.get("/api/v1/does-not-exist", headers={"X-API-Key": "unit-test-key"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_key_comparison_is_constant_time():
    """Guards the `secrets.compare_digest` call: a plain `!=` leaks how many
    leading characters matched via response timing."""
    import inspect

    from app.core import auth

    source = inspect.getsource(auth)
    assert "compare_digest" in source
    assert "x_api_key != settings.api_key" not in source


@pytest.mark.parametrize("route", PUBLIC_ROUTES)
def test_public_routes_stay_public(client, route):
    assert client.get(route).status_code == 200


@pytest.mark.parametrize("route", PUBLIC_ROUTES)
def test_public_routes_do_not_leak_credential_values(monkeypatch, client, route):
    """The catalogue may say a provider is configured; it must never echo the
    value that configures it."""
    secret = "sk-super-secret-value-42"
    monkeypatch.setattr(settings, "gemini_api_key", secret)
    monkeypatch.setattr(settings, "openai_api_key", secret)
    monkeypatch.setattr(settings, "api_key", secret)

    body = client.get(route).text

    assert secret not in body
