#!/usr/bin/env python
"""Answer one question: is it safe to switch this deployment onto its database?

The production cutover is ordering-sensitive. Setting AGENT_OS_*_BACKEND to
postgres before DATABASE_URL resolves, before migrations run, or against a
database stamped for a different environment, breaks the service in ways that
only show up at request time. This checks every precondition FIRST and reports
them together, so the operator flips backends once and it works.

Read-only. It never writes, never migrates, and never mutates configuration.

    uv run python scripts/cutover_preflight.py

Exit 0 = safe to proceed. Exit 1 = at least one blocker; each is named.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

OK, FAIL, WARN = "PASS", "FAIL", "WARN"


def _line(status: str, label: str, detail: str) -> tuple[str, str, str]:
    return (status, label, detail)


async def _check_database() -> list[tuple[str, str, str]]:
    if not settings.database_url:
        return [_line(FAIL, "DATABASE_URL", "not set — nothing to cut over to")]

    rows: list[tuple[str, str, str]] = []
    try:
        from app.persistence.database import AsyncpgDatabase

        db = AsyncpgDatabase.from_settings()
    except Exception as exc:  # noqa: BLE001
        return [_line(FAIL, "DATABASE_URL", f"could not build a client: {exc}")]

    try:
        await db.fetch("SELECT 1")
        rows.append(_line(OK, "database", "reachable"))
    except Exception as exc:  # noqa: BLE001
        await db.close()
        return [*rows, _line(FAIL, "database", f"unreachable: {type(exc).__name__}")]

    try:
        # pgvector must be INSTALLABLE before migration 001, which creates the
        # extension. Discovering this after switching backends is too late.
        available = await db.fetch(
            "SELECT default_version FROM pg_available_extensions WHERE name = 'vector'"
        )
        installed = await db.fetch("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        if installed:
            rows.append(_line(OK, "pgvector", f"installed {installed[0]['extversion']}"))
        elif available:
            rows.append(
                _line(WARN, "pgvector", f"available {available[0]['default_version']}, not yet installed")
            )
        else:
            rows.append(
                _line(FAIL, "pgvector", "not available on this server; migration 001 will fail")
            )

        applied = await db.fetch(
            "SELECT count(*) AS n FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'schema_migrations'"
        )
        if not applied or applied[0]["n"] == 0:
            rows.append(_line(FAIL, "migrations", "never run against this database"))
        else:
            names = await db.fetch("SELECT version FROM schema_migrations ORDER BY version")
            on_disk = sorted(p.name for p in (Path(__file__).resolve().parents[1] / "migrations").glob("*.sql"))
            done = {r["version"] for r in names}
            missing = [m for m in on_disk if m not in done]
            if missing:
                rows.append(_line(FAIL, "migrations", f"{len(missing)} not applied: {', '.join(missing)}"))
            else:
                rows.append(_line(OK, "migrations", f"all {len(on_disk)} applied"))

        stamp = await db.fetch(
            "SELECT count(*) AS n FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'deployment_environment'"
        )
        if stamp and stamp[0]["n"]:
            got = await db.fetch("SELECT environment FROM deployment_environment")
            stamped = got[0]["environment"] if got else None
            if stamped == settings.app_env:
                rows.append(_line(OK, "environment stamp", f"{stamped}"))
            else:
                rows.append(
                    _line(
                        FAIL,
                        "environment stamp",
                        f"database is '{stamped}' but this deployment is "
                        f"'{settings.app_env}' — wrong database",
                    )
                )
        else:
            rows.append(_line(FAIL, "environment stamp", "absent; migration 007 has not run"))
    finally:
        await db.close()

    return rows


async def _check_redis() -> list[tuple[str, str, str]]:
    if settings.queue_backend != "redis" and not settings.redis_url:
        return [_line(WARN, "REDIS_URL", "not set; the queue stays in-memory")]
    if not settings.redis_url:
        return [_line(FAIL, "REDIS_URL", "queue backend is redis but no URL is set")]
    try:
        from app.queue.redis_queue import RedisJobQueue

        queue = RedisJobQueue(settings.redis_url, settings.queue_namespace)
        client = await queue._get_client()
        await client.ping()
        await queue.close()
        return [
            _line(OK, "redis", "reachable"),
            _line(OK, "redis namespace", settings.queue_namespace),
        ]
    except Exception as exc:  # noqa: BLE001
        return [_line(FAIL, "redis", f"unreachable: {type(exc).__name__}")]


async def main() -> int:
    print(f"Deployment environment : {settings.app_env}")
    print(f"Persistence mode       : {settings.persistence_mode}")
    print()

    rows = [*await _check_database(), *await _check_redis()]
    for warning in settings.persistence_warnings():
        rows.append(_line(WARN, "config", warning))

    width = max(len(label) for _, label, _ in rows)
    for status, label, detail in rows:
        print(f"  [{status}] {label.ljust(width)}  {detail}")

    blockers = [r for r in rows if r[0] == FAIL]
    print()
    if blockers:
        print(f"NOT SAFE to switch backends: {len(blockers)} blocker(s) above.")
        return 1
    print("Safe to switch AGENT_OS_*_BACKEND onto postgres/redis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
