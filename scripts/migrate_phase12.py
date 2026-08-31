import asyncio
import os
from pathlib import Path

import asyncpg


async def main():
    dsn = os.environ["DATABASE_URL"]
    sql = Path("migrations/002_phase12_semantic_memory.sql").read_text()
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(sql)
    finally:
        await conn.close()
    print("Phase 12 semantic-memory migration applied.")

asyncio.run(main())
