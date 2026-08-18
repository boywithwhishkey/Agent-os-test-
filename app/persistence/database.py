from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class Database(ABC):
    @abstractmethod
    async def execute(self, query: str, *args: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def close(self) -> None:
        return None


class AsyncpgDatabase(Database):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool = None

    @classmethod
    def from_env(cls) -> "AsyncpgDatabase":
        dsn = os.getenv("DATABASE_URL", "").strip()
        if not dsn:
            raise RuntimeError("DATABASE_URL is required for PostgreSQL persistence")
        return cls(dsn)

    async def _get_pool(self):
        if self._pool is None:
            try:
                import asyncpg
            except ImportError as exc:
                raise RuntimeError(
                    'asyncpg is required for PostgreSQL. Run: pip install -e ".[dev]"'
                ) from exc
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=int(os.getenv("AGENT_OS_DB_POOL_MIN", "1")),
                max_size=int(os.getenv("AGENT_OS_DB_POOL_MAX", "10")),
                command_timeout=float(os.getenv("AGENT_OS_DB_COMMAND_TIMEOUT", "30")),
            )
        return self._pool

    async def execute(self, query: str, *args: Any) -> str:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
