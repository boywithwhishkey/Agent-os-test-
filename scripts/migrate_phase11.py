from __future__ import annotations

import asyncio
import os
from pathlib import Path


async def main() -> None:
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        raise SystemExit("DATABASE_URL is required")

    try:
        import asyncpg
    except ImportError as exc:
        raise SystemExit('Install dependencies first: pip install -e ".[dev]"') from exc

    migration = Path("migrations/001_phase11_durable_core.sql").read_text()
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(migration)
    finally:
        await conn.close()

    print("Phase 11 database migration applied.")


if __name__ == "__main__":
    asyncio.run(main())
