from __future__ import annotations

from pathlib import Path

from app.persistence.database import Database

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
_LOCK_KEY = "agent_os_migrations"


async def run_migrations(database: Database, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply pending .sql migrations under an advisory lock, tracked by filename."""
    await database.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    await database.execute("SELECT pg_advisory_lock(hashtext($1))", _LOCK_KEY)
    try:
        applied_rows = await database.fetch("SELECT version FROM schema_migrations")
        applied = {row["version"] for row in applied_rows}

        newly_applied: list[str] = []
        for path in sorted(migrations_dir.glob("*.sql")):
            if path.name in applied:
                continue
            await database.execute(path.read_text())
            await database.execute(
                "INSERT INTO schema_migrations (version) VALUES ($1)",
                path.name,
            )
            newly_applied.append(path.name)
        return newly_applied
    finally:
        await database.execute("SELECT pg_advisory_unlock(hashtext($1))", _LOCK_KEY)
