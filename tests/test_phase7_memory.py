import pytest

from app.memory.in_memory import InMemoryMemoryStore
from app.memory.models import MemoryQuery, MemoryScope, MemoryWrite
from app.memory.service import MemoryService
from app.services.context_injection import ContextInjector


@pytest.mark.asyncio
async def test_memory_write_and_get():
    store = InMemoryMemoryStore()
    service = MemoryService(store)
    record = await service.remember(
        MemoryWrite(
            scope=MemoryScope.PROJECT,
            key="stack",
            content="Use Python and FastAPI",
            project_id="agent-os",
        )
    )
    fetched = await store.get(record.id)
    assert fetched is not None
    assert fetched.content == "Use Python and FastAPI"


@pytest.mark.asyncio
async def test_memory_search_respects_project_scope():
    service = MemoryService(InMemoryMemoryStore())
    await service.remember(
        MemoryWrite(
            scope=MemoryScope.DECISION,
            key="provider",
            content="Use Gemini free tier",
            project_id="agent-os",
        )
    )
    await service.remember(
        MemoryWrite(
            scope=MemoryScope.DECISION,
            key="provider",
            content="Use another provider",
            project_id="other",
        )
    )
    result = await service.recall(MemoryQuery(project_id="agent-os"))
    assert len(result) == 1
    assert result[0].content == "Use Gemini free tier"


@pytest.mark.asyncio
async def test_memory_search_uses_text_and_tags():
    service = MemoryService(InMemoryMemoryStore())
    await service.remember(
        MemoryWrite(
            scope=MemoryScope.PROJECT,
            key="architecture",
            content="PostgreSQL will be the durable persistence layer",
            tags=["database", "future"],
        )
    )
    result = await service.recall(
        MemoryQuery(query="PostgreSQL", tags=["database"])
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_context_is_rendered_for_agents():
    service = MemoryService(InMemoryMemoryStore())
    await service.remember(
        MemoryWrite(
            scope=MemoryScope.PROJECT,
            key="fastapi",
            content="FastAPI is the API framework",
            project_id="agent-os",
        )
    )
    context = await service.build_context(
        MemoryQuery(query="FastAPI", project_id="agent-os")
    )
    assert "[project:fastapi]" in context.rendered


@pytest.mark.asyncio
async def test_context_injector_is_backend_independent():
    service = MemoryService(InMemoryMemoryStore())
    await service.remember(
        MemoryWrite(
            scope=MemoryScope.DECISION,
            key="security",
            content="High-risk tools require trusted approval",
            project_id="agent-os",
        )
    )
    injector = ContextInjector(service)
    context = await injector.for_task(
        objective="security approval",
        project_id="agent-os",
    )
    assert "RELEVANT MEMORY:" in context
    assert "trusted approval" in context


@pytest.mark.asyncio
async def test_memory_search_matches_relevant_query_tokens():
    service = MemoryService(InMemoryMemoryStore())
    await service.remember(
        MemoryWrite(
            scope=MemoryScope.DECISION,
            key="security",
            content="High-risk tools require trusted approval",
            project_id="agent-os",
        )
    )
    result = await service.recall(
        MemoryQuery(query="security approval", project_id="agent-os")
    )
    assert len(result) == 1
    assert "trusted approval" in result[0].content
