from __future__ import annotations

import time

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.persistence.database import Database


class PostgresAdapter(IntegrationAdapter):
    """Verifies DATABASE_URL is reachable with a trivial `SELECT 1`,
    independent of whether Postgres is the currently active backend for any
    given feature (see app.core.readiness for that separate, narrower
    check)."""

    def __init__(self, *, database_url: str | None = None, database: Database | None = None) -> None:
        self.database_url = database_url or settings.database_url
        self._database = database
        if not self._database and not self.database_url:
            raise RuntimeError("DATABASE_URL is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.POSTGRESQL,
            request,
            reason="PostgreSQL is a storage backend, not a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_database = self._database is None
        if self._database is not None:
            database = self._database
        else:
            from app.persistence.database import AsyncpgDatabase

            database = AsyncpgDatabase(self.database_url)

        started = time.perf_counter()
        try:
            await database.fetch("SELECT 1")
            return True, (time.perf_counter() - started) * 1000, None
        except Exception as exc:  # noqa: BLE001 - any backend failure means "not reachable"
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_database:
                await database.close()
