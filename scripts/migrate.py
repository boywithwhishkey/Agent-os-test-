from __future__ import annotations

import asyncio
import sys

from app.core.config import settings
from app.persistence.database import AsyncpgDatabase
from app.persistence.environment import EnvironmentMismatchError, ensure_environment
from app.persistence.migrations import run_migrations


async def main() -> None:
    database = AsyncpgDatabase.from_settings()
    try:
        # Verify environment ownership BEFORE touching schema: migrating
        # production from a staging deployment is exactly the accident this
        # guard exists to prevent.
        environment = await ensure_environment(database, settings.app_env)
        applied = await run_migrations(database)
    finally:
        await database.close()

    print(f"Environment: {environment}")

    if applied:
        print(f"Applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("Database is already up to date.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except EnvironmentMismatchError as exc:
        # A deploy pipeline reads this: print the reason plainly and fail with a
        # non-zero status rather than dumping a traceback.
        print(f"ENVIRONMENT MISMATCH: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
