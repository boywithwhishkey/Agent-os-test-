"""Guards against a production-like deployment degrading silently.

The failure mode: a service starts with no DATABASE_URL, falls back to
in-memory stores, reports healthy, and loses every task, workflow, approval
and audit record on each restart — which is what api.thynact.com does today.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app

client = TestClient(app)


def test_app_env_rejects_unknown_values():
    for bad in ["prod", "Staging!", "live", ""]:
        with pytest.raises(ValueError):
            Settings(AGENT_OS_APP_ENV=bad)


def test_app_env_normalizes_case_and_padding():
    assert Settings(AGENT_OS_APP_ENV=" Production ").app_env == "production"


def test_ephemeral_subsystems_are_enumerated():
    s = Settings()  # defaults are all memory
    assert s.persistence_mode == "ephemeral"
    assert "task" in s.ephemeral_subsystems and "queue" in s.ephemeral_subsystems


def test_partial_persistence_is_reported_distinctly():
    s = Settings(AGENT_OS_TASK_BACKEND="postgres")
    assert s.persistence_mode == "partial"
    assert "task" not in s.ephemeral_subsystems


def test_production_with_memory_backends_produces_a_warning():
    s = Settings(AGENT_OS_APP_ENV="production")
    warnings = s.persistence_warnings()
    assert any("lost on every restart" in w for w in warnings)


def test_development_with_memory_backends_is_not_warned_about():
    # Ephemeral local development is normal, not a misconfiguration.
    assert Settings(AGENT_OS_APP_ENV="development").persistence_warnings() == []


def test_selected_postgres_backend_without_database_url_is_flagged():
    s = Settings(AGENT_OS_APP_ENV="staging", AGENT_OS_MEMORY_BACKEND="postgres", DATABASE_URL="")
    assert any("DATABASE_URL" in w for w in s.persistence_warnings())


def test_selected_redis_queue_without_redis_url_is_flagged():
    s = Settings(AGENT_OS_APP_ENV="staging", AGENT_OS_QUEUE_BACKEND="redis", REDIS_URL="")
    assert any("REDIS_URL" in w for w in s.persistence_warnings())


def test_health_reports_persistence_mode_and_warnings():
    body = client.get("/health").json()
    assert body["persistence"] in {"durable", "partial", "ephemeral"}
    assert isinstance(body["warnings"], list)


def test_liveness_is_independent_of_dependencies():
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_fails_when_durability_is_required_but_absent(monkeypatch):
    from app.core import readiness as readiness_module

    monkeypatch.setattr(
        readiness_module.settings, "require_durable_persistence", True, raising=False
    )
    checks = await readiness_module.check_readiness()
    assert checks["persistence"] == "ephemeral"


def test_queue_namespace_is_environment_scoped():
    assert Settings(AGENT_OS_APP_ENV="production").queue_namespace == "agent-os:production"
    assert Settings(AGENT_OS_APP_ENV="staging").queue_namespace == "agent-os:staging"


def test_security_headers_are_present():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_docs_are_public_outside_production():
    for env in ["development", "staging"]:
        assert Settings(AGENT_OS_APP_ENV=env).docs_enabled is True


def test_docs_are_closed_in_production_by_default():
    # api.thynact.com is publicly reachable; publishing the whole route surface
    # to anonymous callers is not a sensible production default.
    assert Settings(AGENT_OS_APP_ENV="production").docs_enabled is False


def test_docs_can_be_explicitly_re_enabled_in_production():
    assert (
        Settings(AGENT_OS_APP_ENV="production", AGENT_OS_ENABLE_DOCS="true").docs_enabled is True
    )
