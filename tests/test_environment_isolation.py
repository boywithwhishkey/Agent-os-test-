"""Production/staging isolation guards.

The failure these prevent is a misconfigured DATABASE_URL pointing a staging
deployment at the production database, which otherwise succeeds silently.
"""

import pytest

from app.core.config import Settings
from app.persistence.environment import EnvironmentMismatchError, ensure_environment


class FakeStampDatabase:
    """Minimal Database stand-in holding a single environment stamp."""

    def __init__(self, stamp: str | None = None):
        self.stamp = stamp
        self.executed: list[str] = []

    async def execute(self, query, *args):
        self.executed.append(query)
        if "INSERT INTO deployment_environment" in query and self.stamp is None:
            self.stamp = args[0]
        return "OK"

    async def fetchrow(self, query, *args):
        if self.stamp is None:
            return None
        return {"environment": self.stamp}

    async def fetch(self, query, *args):
        return []

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_stamps_an_unstamped_database():
    db = FakeStampDatabase()
    assert await ensure_environment(db, "staging") == "staging"
    assert db.stamp == "staging"


@pytest.mark.asyncio
async def test_accepts_a_matching_stamp():
    db = FakeStampDatabase(stamp="production")
    assert await ensure_environment(db, "production") == "production"


@pytest.mark.asyncio
async def test_rejects_staging_pointed_at_the_production_database():
    db = FakeStampDatabase(stamp="production")
    with pytest.raises(EnvironmentMismatchError) as exc:
        await ensure_environment(db, "staging")
    # The message has to name both sides — this is read by whoever is paging
    # through a failed deploy log.
    assert "production" in str(exc.value)
    assert "staging" in str(exc.value)


@pytest.mark.asyncio
async def test_rejects_production_pointed_at_the_staging_database():
    db = FakeStampDatabase(stamp="staging")
    with pytest.raises(EnvironmentMismatchError):
        await ensure_environment(db, "production")


@pytest.mark.asyncio
async def test_stamp_comparison_ignores_case_and_padding():
    db = FakeStampDatabase(stamp="Production ")
    assert await ensure_environment(db, "PRODUCTION") == "production"


@pytest.mark.asyncio
async def test_empty_environment_is_rejected():
    db = FakeStampDatabase()
    with pytest.raises(ValueError):
        await ensure_environment(db, "   ")


def test_queue_namespace_separates_environments():
    prod = Settings(AGENT_OS_APP_ENV="production")
    staging = Settings(AGENT_OS_APP_ENV="staging")
    assert prod.queue_namespace != staging.queue_namespace
    assert prod.queue_namespace == "agent-os:production"
    assert staging.queue_namespace == "agent-os:staging"
