"""Environment ownership guard for the application database.

Production and staging must not share a database, Redis, or queue state. A
misconfigured ``DATABASE_URL`` is the realistic way that happens, and it fails
silently — staging writes into production tables and nobody notices until the
damage is real.

This module stamps the database with the environment that first used it and
refuses to proceed when a differently-labelled deployment connects to it later.
The stamp lives in the database rather than in configuration precisely so that
it cannot be lost by editing an environment variable.
"""

from __future__ import annotations

from app.persistence.database import Database


class EnvironmentMismatchError(RuntimeError):
    """Raised when a deployment connects to another environment's database."""


async def ensure_environment(database: Database, environment: str) -> str:
    """Stamp the database on first use, or verify an existing stamp.

    Returns the environment the database is stamped with. Raises
    :class:`EnvironmentMismatchError` when the stamp names a different
    environment, which is the case this guard exists to catch.
    """
    environment = environment.strip().lower()
    if not environment:
        raise ValueError("environment must be a non-empty string")

    await database.execute(
        """
        CREATE TABLE IF NOT EXISTS deployment_environment (
            id BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id),
            environment TEXT NOT NULL,
            stamped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    row = await database.fetchrow("SELECT environment FROM deployment_environment WHERE id")
    if row is None:
        await database.execute(
            "INSERT INTO deployment_environment (id, environment) VALUES (TRUE, $1) "
            "ON CONFLICT (id) DO NOTHING",
            environment,
        )
        # Re-read rather than assuming the insert won: two deployments racing on
        # a fresh database must agree on whichever stamp actually landed.
        row = await database.fetchrow("SELECT environment FROM deployment_environment WHERE id")
        if row is None:  # pragma: no cover - only if the row vanished mid-race
            raise EnvironmentMismatchError("could not stamp the database environment")

    stamped = str(row["environment"]).strip().lower()
    if stamped != environment:
        raise EnvironmentMismatchError(
            f"This database belongs to the '{stamped}' environment but the running "
            f"deployment is '{environment}'. Refusing to continue: production and "
            f"staging must not share a database. Point DATABASE_URL at the "
            f"'{environment}' database, or correct AGENT_OS_APP_ENV."
        )
    return stamped
