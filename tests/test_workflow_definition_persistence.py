import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.persistence.database import Database
from app.persistence.postgres_stores import PostgresWorkflowDefinitionStore
from app.workflows.definition_store import InMemoryWorkflowDefinitionStore
from app.workflows.factory import build_workflow_definition_store
from app.workflows.models import StepType, WorkflowDefinition, WorkflowStep

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


def make_definition() -> WorkflowDefinition:
    return WorkflowDefinition(
        name="durable-definitions",
        steps=[WorkflowStep(id="step-1", type=StepType.NOOP)],
    )


class FakeDatabase(Database):
    def __init__(self):
        self.executed = []
        self.rows = {}

    async def execute(self, query, *args):
        self.executed.append((query, args))
        return "OK"

    async def fetchrow(self, query, *args):
        self.executed.append((query, args))
        return self.rows.get(args[0]) if args else None

    async def fetch(self, query, *args):
        self.executed.append((query, args))
        return []


@pytest.mark.asyncio
async def test_in_memory_definition_store_roundtrip():
    store = InMemoryWorkflowDefinitionStore()
    definition = make_definition()
    await store.save(definition)
    loaded = await store.get(definition.id)
    assert loaded.id == definition.id
    assert loaded.name == "durable-definitions"


@pytest.mark.asyncio
async def test_in_memory_definition_store_unknown_id_returns_none():
    store = InMemoryWorkflowDefinitionStore()
    assert await store.get("missing") is None


@pytest.mark.asyncio
async def test_postgres_definition_store_save_and_get():
    db = FakeDatabase()
    store = PostgresWorkflowDefinitionStore(db)
    definition = make_definition()
    await store.save(definition)
    assert "INSERT INTO workflow_definitions" in db.executed[0][0]

    db.rows[definition.id] = {"payload": definition.model_dump(mode="json")}
    loaded = await store.get(definition.id)
    assert loaded.id == definition.id


@pytest.mark.asyncio
async def test_postgres_definition_store_unknown_id_returns_none():
    db = FakeDatabase()
    store = PostgresWorkflowDefinitionStore(db)
    assert await store.get("missing") is None


def test_workflow_definition_backend_defaults_to_in_memory():
    assert isinstance(build_workflow_definition_store(), InMemoryWorkflowDefinitionStore)


def test_unsupported_workflow_definition_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "workflow_definition_backend", "not-a-backend")
    with pytest.raises(RuntimeError, match="Unsupported workflow definition backend"):
        build_workflow_definition_store()


def test_postgres_workflow_definition_backend_requires_database_url(monkeypatch):
    monkeypatch.setattr(settings, "workflow_definition_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        build_workflow_definition_store()


def test_run_and_resume_workflow_via_api(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "test-api-key")
    definition = make_definition().model_dump(mode="json")

    run_response = client.post(
        "/api/v1/workflows/run",
        headers=AUTH_HEADERS,
        json={"definition": definition, "context": {}},
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["status"] == "completed"

    get_response = client.get(
        f"/api/v1/workflows/runs/{run['id']}", headers=AUTH_HEADERS
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == run["id"]
