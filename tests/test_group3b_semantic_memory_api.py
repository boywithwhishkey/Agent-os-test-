import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.memory.models import MemoryQuery, MemoryScope
from app.persistence.database import Database
from app.persistence.postgres_stores import PostgresMemoryStore

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


def test_memory_write_search_and_context_round_trip_over_http():
    write_response = client.post(
        "/api/v1/memory",
        headers=AUTH_HEADERS,
        json={
            "scope": "project",
            "key": "architecture",
            "content": "Agent OS uses a hybrid semantic memory service",
            "project_id": "agent-os",
        },
    )
    assert write_response.status_code == 201

    search_response = client.post(
        "/api/v1/memory/search",
        headers=AUTH_HEADERS,
        json={"query": "hybrid semantic memory", "project_id": "agent-os", "limit": 5},
    )
    assert search_response.status_code == 200
    keys = [record["key"] for record in search_response.json()]
    assert "architecture" in keys

    context_response = client.post(
        "/api/v1/memory/context",
        headers=AUTH_HEADERS,
        json={"query": "hybrid semantic memory", "project_id": "agent-os", "limit": 5},
    )
    assert context_response.status_code == 200
    body = context_response.json()
    assert "rendered" in body
    assert "records" in body
    assert "architecture" in body["rendered"]


class FakeDatabase(Database):
    def __init__(self):
        self.executed = []

    async def execute(self, query, *args):
        self.executed.append((query, args))
        return "OK"

    async def fetchrow(self, query, *args):
        return None

    async def fetch(self, query, *args):
        self.executed.append((query, args))
        return []


@pytest.mark.asyncio
async def test_semantic_search_applies_scope_and_tag_filters():
    db = FakeDatabase()
    store = PostgresMemoryStore(db)

    await store.semantic_search(
        query=MemoryQuery(
            scopes=[MemoryScope.PROJECT, MemoryScope.DECISION],
            tags=["security"],
            limit=5,
        ),
        vector=[0.1, 0.2],
        limit=5,
    )

    query, args = db.executed[-1]
    assert "scope = ANY($1::text[])" in query
    assert "tags &&" in query
    assert args[0] == ["project", "decision"]
    assert args[1] == ["security"]


@pytest.mark.asyncio
async def test_semantic_search_without_filters_still_binds_vector():
    db = FakeDatabase()
    store = PostgresMemoryStore(db)

    await store.semantic_search(
        query=MemoryQuery(limit=3),
        vector=[0.5, 0.5],
        limit=3,
    )

    query, args = db.executed[-1]
    assert "embedding IS NOT NULL" in query
    assert args[0].startswith("[0.5")
