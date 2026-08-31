"""Static checks on render.yaml.

The blueprint cannot be validated against Render without an API key, so these
checks assert the invariants that matter to us and would otherwise only be
discovered during a failed sync or, worse, after a bad deploy:

  * the blueprint stays STAGING-ONLY (never declares production resources)
  * staging never points at production hostnames
  * the environment identity and durability guards are actually set
  * datastore connections come from the staging instances, not literals
  * no secret values are committed

Run: uv run python scripts/validate_deploy_config.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RENDER_YAML = ROOT / "render.yaml"

PRODUCTION_HOSTS = {"api.thynact.com", "app.thynact.com"}
# Values that must never be committed as literals.
SECRET_KEYS = {
    "AGENT_OS_API_KEY",
    "GITHUB_OAUTH_CLIENT_ID",
    "GITHUB_OAUTH_CLIENT_SECRET",
    "GITLAB_OAUTH_CLIENT_SECRET",
    "SLACK_OAUTH_CLIENT_SECRET",
    "NOTION_OAUTH_CLIENT_SECRET",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "CLOUDFLARE_API_TOKEN",
    "RENDER_API_KEY",
}


def validate(spec: dict) -> list[str]:
    errors: list[str] = []
    services = spec.get("services") or []
    databases = spec.get("databases") or []

    web = [s for s in services if s.get("type") == "web"]
    if len(web) != 1:
        errors.append(f"expected exactly one web service (staging), found {len(web)}")

    for service in services:
        name = service.get("name", "<unnamed>")
        # Staging-only invariant: nothing may track main or be named production.
        if service.get("branch") not in (None, "staging"):
            errors.append(f"{name}: branch must be 'staging', got {service.get('branch')!r}")
        if "prod" in name.lower():
            errors.append(f"{name}: production resources must not be blueprint-managed")

        env_vars = {v["key"]: v for v in service.get("envVars", []) if "key" in v}

        if service.get("type") != "web":
            continue

        if not service.get("healthCheckPath"):
            errors.append(f"{name}: healthCheckPath is required")

        app_env = env_vars.get("AGENT_OS_APP_ENV", {}).get("value")
        if app_env != "staging":
            errors.append(f"{name}: AGENT_OS_APP_ENV must be 'staging', got {app_env!r}")

        if env_vars.get("AGENT_OS_REQUIRE_DURABLE_PERSISTENCE", {}).get("value") != "true":
            errors.append(f"{name}: AGENT_OS_REQUIRE_DURABLE_PERSISTENCE must be 'true'")

        # Datastores must be injected from the staging instances, never literals.
        if "fromDatabase" not in env_vars.get("DATABASE_URL", {}):
            errors.append(f"{name}: DATABASE_URL must come from fromDatabase")
        if "fromService" not in env_vars.get("REDIS_URL", {}):
            errors.append(f"{name}: REDIS_URL must come from fromService")

        for key, var in env_vars.items():
            value = var.get("value")
            if not isinstance(value, str):
                continue
            for host in PRODUCTION_HOSTS:
                # Substring check would false-positive on api-staging.thynact.com,
                # so compare the hostnames the value actually points at.
                if any(part == host for part in value.replace("//", " ").replace("/", " ").split()):
                    errors.append(f"{name}: {key} points at production host {host}")
            if key in SECRET_KEYS and value:
                errors.append(f"{name}: {key} must use 'sync: false', not a committed value")

    for database in databases:
        name = database.get("name", "<unnamed>")
        if "prod" in name.lower():
            errors.append(f"{name}: production databases must not be blueprint-managed")

    if not databases:
        errors.append("staging must declare its own database, not share production's")
    if not any(s.get("type") == "redis" for s in services):
        errors.append("staging must declare its own Redis instance")

    return errors


def main() -> int:
    if not RENDER_YAML.exists():
        print(f"MISSING: {RENDER_YAML}", file=sys.stderr)
        return 1
    spec = yaml.safe_load(RENDER_YAML.read_text())
    errors = validate(spec)
    if errors:
        print("render.yaml validation FAILED:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("render.yaml OK: staging-only, isolated datastores, no committed secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
