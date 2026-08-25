from __future__ import annotations

import asyncio

from app.persistence.database import AsyncpgDatabase
from app.persistence.migrations import run_migrations


async def main() -> None:
    database = AsyncpgDatabase.from_settings()
    try:
        applied = await run_migrations(database)
    finally:
        await database.close()

    if applied:
        print(f"Applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("Database is already up to date.")


if __name__ == "__main__":
    asyncio.run(main())
