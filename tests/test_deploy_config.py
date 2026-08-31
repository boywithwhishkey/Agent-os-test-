"""render.yaml invariants, plus proof the validator catches violations.

A validator that only ever passes is worthless, so each check is exercised
against a deliberately broken spec.
"""

import copy
import importlib.util
from pathlib import Path

import yaml

# scripts/ is a script directory, not an importable package (pyproject excludes
# it from the wheel), so load the validator by path rather than restructuring it.
_spec = importlib.util.spec_from_file_location(
    "validate_deploy_config",
    Path(__file__).resolve().parent.parent / "scripts" / "validate_deploy_config.py",
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
RENDER_YAML = _module.RENDER_YAML
validate = _module.validate


def load() -> dict:
    return yaml.safe_load(RENDER_YAML.read_text())


def test_committed_blueprint_is_valid():
    assert validate(load()) == []


def test_blueprint_declares_staging_datastores():
    spec = load()
    assert any(s["type"] == "redis" for s in spec["services"])
    assert spec["databases"], "staging needs its own database"


def test_no_service_tracks_main():
    for service in load()["services"]:
        assert service.get("branch") in (None, "staging")


def test_rejects_a_service_tracking_main():
    spec = load()
    spec["services"][0]["branch"] = "main"
    assert any("branch must be 'staging'" in e for e in validate(spec))


def test_rejects_production_named_resources():
    spec = load()
    spec["databases"].append({"name": "thynact-prod-db", "plan": "basic-256mb"})
    assert any("must not be blueprint-managed" in e for e in validate(spec))


def test_rejects_pointing_at_the_production_api():
    spec = load()
    for var in spec["services"][0]["envVars"]:
        if var["key"] == "AGENT_OS_OAUTH_REDIRECT_BASE_URL":
            var["value"] = "https://api.thynact.com"
    assert any("production host" in e for e in validate(spec))


def test_staging_hostnames_are_not_mistaken_for_production():
    # api-staging.thynact.com contains "thynact.com" but is NOT production;
    # the check must not false-positive on it.
    assert validate(load()) == []


def test_rejects_a_committed_secret_value():
    spec = load()
    spec["services"][0]["envVars"].append({"key": "AGENT_OS_API_KEY", "value": "oops"})
    assert any("must use 'sync: false'" in e for e in validate(spec))


def test_rejects_missing_durability_requirement():
    spec = load()
    spec["services"][0]["envVars"] = [
        v for v in spec["services"][0]["envVars"]
        if v["key"] != "AGENT_OS_REQUIRE_DURABLE_PERSISTENCE"
    ]
    assert any("REQUIRE_DURABLE_PERSISTENCE" in e for e in validate(spec))


def test_rejects_a_literal_database_url():
    spec = copy.deepcopy(load())
    for var in spec["services"][0]["envVars"]:
        if var["key"] == "DATABASE_URL":
            var.pop("fromDatabase")
            var["value"] = "postgresql://user:pass@host/db"
    assert any("must come from fromDatabase" in e for e in validate(spec))


def test_rejects_wrong_app_env():
    spec = load()
    for var in spec["services"][0]["envVars"]:
        if var["key"] == "AGENT_OS_APP_ENV":
            var["value"] = "production"
    assert any("AGENT_OS_APP_ENV must be 'staging'" in e for e in validate(spec))
