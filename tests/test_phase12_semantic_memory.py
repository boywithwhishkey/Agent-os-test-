from datetime import UTC, datetime

import pytest

from app.embeddings.deterministic import DeterministicEmbeddingProvider
from app.memory.models import MemoryQuery, MemoryRecord, MemoryScope, MemoryWrite
from app.memory.semantic import RankedMemory, SemanticMemoryService, compress_ranked_memories


class FakeStore:
    def __init__(self, records):
        self.records = records
        self.embeddings = {}
    async def set_embedding(self, memory_id, vector):
        self.embeddings[memory_id] = vector
    async def semantic_search(self, query, vector, limit):
        return [(r, max(0.0, 1-i*0.2)) for i, r in enumerate(self.records[:limit])]

class FakeMemory:
    def __init__(self, records):
        self.records = records
        self.store = FakeStore(records)
    async def remember(self, memory):
        r = MemoryRecord(**memory.model_dump())
        self.records.append(r)
        return r
    async def recall(self, query):
        return self.records[:query.limit]

def rec(key, content, importance=0.5):
    return MemoryRecord(
        scope=MemoryScope.PROJECT, key=key, content=content,
        project_id="agent-os", importance=importance,
        created_at=datetime.now(UTC),
    )

@pytest.mark.asyncio
async def test_embedding_stable():
    p = DeterministicEmbeddingProvider(16)
    assert await p.embed("semantic memory") == await p.embed("semantic memory")

@pytest.mark.asyncio
async def test_remember_sets_embedding():
    m = FakeMemory([])
    s = SemanticMemoryService(m, DeterministicEmbeddingProvider(8))
    r = await s.remember(MemoryWrite(
        scope=MemoryScope.PROJECT, key="db", content="postgres memory",
        project_id="agent-os"
    ))
    assert r.id in m.store.embeddings

@pytest.mark.asyncio
async def test_hybrid_ranking():
    m = FakeMemory([rec("postgres", "durable memory", .9), rec("redis", "queue", .2)])
    s = SemanticMemoryService(m, DeterministicEmbeddingProvider(8))
    ranked = await s.hybrid_recall(MemoryQuery(project_id="agent-os", query="durable memory", limit=2))
    assert ranked[0].record.key == "postgres"

@pytest.mark.asyncio
async def test_recall_returns_records():
    s = SemanticMemoryService(FakeMemory([rec("decision", "use pgvector")]), DeterministicEmbeddingProvider(8))
    result = await s.recall(MemoryQuery(project_id="agent-os", query="pgvector", limit=1))
    assert result[0].key == "decision"

def test_compression_budget():
    text = compress_ranked_memories([RankedMemory(rec("a", "A"*200), .9)], 100)
    assert len(text) <= 100

@pytest.mark.asyncio
async def test_build_context():
    s = SemanticMemoryService(FakeMemory([rec("db", "durable memory")]), DeterministicEmbeddingProvider(8))
    context = await s.build_context(
        MemoryQuery(project_id="agent-os", query="durable memory", limit=1), 500
    )
    assert "score=" in context.rendered
    assert context.records[0].key == "db"
