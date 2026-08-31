import pytest

from app.core.config import settings
from app.integrations.models import IntegrationRequest
from app.integrations.postgresql import PostgresAdapter
from app.integrations.redis import RedisAdapter


class FakeDatabase:
    def __init__(self, *, fails: bool = False):
        self.fails = fails
        self.closed = False

    async def fetch(self, query, *args):
        if self.fails:
            raise ConnectionError("could not connect to server")
        return [{"?column?": 1}]

    async def close(self):
        self.closed = True


class FakeRedisClient:
    def __init__(self, *, fails: bool = False):
        self.fails = fails

    async def ping(self):
        if self.fails:
            raise ConnectionError("connection refused")
        return True


class FakeQueue:
    def __init__(self, *, fails: bool = False):
        self._client = FakeRedisClient(fails=fails)
        self.closed = False

    async def _get_client(self):
        return self._client

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_postgres_adapter_reports_reachable():
    database = FakeDatabase()
    adapter = PostgresAdapter(database=database)
    connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None
    assert database.closed is False  # injected database is caller-owned


@pytest.mark.asyncio
async def test_postgres_adapter_reports_failure():
    database = FakeDatabase(fails=True)
    adapter = PostgresAdapter(database=database)
    connected, latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert latency_ms is None
    assert "could not connect" in (error or "")


@pytest.mark.asyncio
async def test_postgres_adapter_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "database_url", "")
    with pytest.raises(RuntimeError):
        PostgresAdapter(database_url="")


@pytest.mark.asyncio
async def test_postgres_adapter_execute_is_unsupported():
    adapter = PostgresAdapter(database=FakeDatabase())
    result = await adapter.execute(IntegrationRequest(workflow="anything"))
    assert result.success is False


@pytest.mark.asyncio
async def test_redis_adapter_reports_reachable():
    queue = FakeQueue()
    adapter = RedisAdapter(queue=queue)
    connected, latency_ms, error = await adapter.test_connection()

    assert connected is True
    assert latency_ms is not None
    assert error is None


@pytest.mark.asyncio
async def test_redis_adapter_reports_failure():
    queue = FakeQueue(fails=True)
    adapter = RedisAdapter(queue=queue)
    connected, _latency_ms, error = await adapter.test_connection()

    assert connected is False
    assert "connection refused" in (error or "")


@pytest.mark.asyncio
async def test_redis_adapter_requires_redis_url(monkeypatch):
    # The adapter falls back to settings.redis_url, so the ambient environment
    # has to be cleared for this to test what it claims to test. Without this
    # the test silently passes only on machines with no REDIS_URL set.
    monkeypatch.setattr("app.integrations.redis.settings.redis_url", "")
    with pytest.raises(RuntimeError):
        RedisAdapter(redis_url="")
