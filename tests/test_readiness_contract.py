"""/ready must not claim durable readiness it does not have.

The bug this locks out: check_readiness() only added an entry for a backend
that had been explicitly selected, so an all-in-memory deployment produced an
EMPTY dict — and `all(...)` over an empty dict is vacuously true. /ready
answered 200 {"status": "ready", "checks": {}} for a service that loses every
task, workflow, approval and audit record on restart.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_all_in_memory_is_reported_degraded_not_ready(client):
    body = client.get("/ready").json()

    assert body["status"] == "degraded"
    assert body["checks"]["persistence"] == "ephemeral"
    assert body["checks"] != {}


def test_all_in_memory_still_serves_traffic(client):
    """The HTTP status gates routing, and must NOT start failing the moment
    AGENT_OS_APP_ENV flips to production but before a database exists — that
    would take the live service down as a side effect of a config change."""
    assert client.get("/ready").status_code == 200


def test_ephemeral_is_fatal_once_durability_is_explicitly_required(monkeypatch, client):
    monkeypatch.setattr(settings, "require_durable_persistence", True)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_unavailable_dependency_fails_the_http_status(monkeypatch, client):
    import app.core.readiness as readiness_module

    monkeypatch.setattr(settings, "memory_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "postgres://bad-host/db")

    async def fake_check_database():
        return "unavailable"

    monkeypatch.setattr(readiness_module, "_check_database", fake_check_database)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "unavailable"


def test_health_reports_ephemeral_persistence(client):
    body = client.get("/health").json()

    assert body["persistence"] == "ephemeral"


def test_production_with_memory_backends_emits_a_warning(monkeypatch):
    """The warning is what makes a silently-ephemeral production visible. It is
    suppressed today only because app_env is still 'development'."""
    monkeypatch.setattr(settings, "app_env", "production")

    warnings = settings.persistence_warnings()

    assert any("lost on every restart" in w for w in warnings)


def test_docs_are_disabled_in_production_by_default(monkeypatch):
    """api.thynact.com is public; /docs would publish the whole route surface.
    Currently open ONLY because app_env is 'development'."""
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "enable_docs", None)

    assert settings.docs_enabled is False

    monkeypatch.setattr(settings, "app_env", "staging")
    assert settings.docs_enabled is True


def test_unknown_app_env_is_rejected():
    """A typo like 'prod' would silently create a third environment that shares
    neither the Redis namespace nor the database stamp of the real one."""
    from pydantic import ValidationError

    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(AGENT_OS_APP_ENV="prod")


def test_queue_namespace_is_environment_scoped(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    assert settings.queue_namespace == "agent-os:production"

    monkeypatch.setattr(settings, "app_env", "staging")
    assert settings.queue_namespace == "agent-os:staging"


def test_redis_queue_requires_an_explicit_namespace():
    """The prefix used to default to the bare "agent-os" — no environment
    suffix — so a direct construction shared one key space across production
    and staging. It is now a required argument."""
    import inspect

    from app.queue.redis_queue import RedisJobQueue

    prefix = inspect.signature(RedisJobQueue.__init__).parameters["prefix"]
    assert prefix.default is inspect.Parameter.empty
