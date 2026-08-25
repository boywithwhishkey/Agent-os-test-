import pytest

from app.core.config import settings
from app.persistence.postgres_stores import PostgresExecutionStore, PostgresWorkflowRunStore
from app.runtime.factory import build_execution_store
from app.runtime.store import InMemoryExecutionStore
from app.workflows.factory import build_workflow_run_store
from app.workflows.store import InMemoryWorkflowRunStore


def test_workflow_store_defaults_to_in_memory():
    store = build_workflow_run_store()

    assert isinstance(store, InMemoryWorkflowRunStore)


def test_workflow_store_selects_postgres(monkeypatch):
    monkeypatch.setattr(settings, "workflow_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "postgres://user:pass@localhost/db")

    store = build_workflow_run_store()

    assert isinstance(store, PostgresWorkflowRunStore)


def test_unsupported_workflow_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "workflow_backend", "not-a-backend")

    with pytest.raises(RuntimeError, match="Unsupported workflow backend"):
        build_workflow_run_store()


def test_runtime_store_defaults_to_in_memory():
    store = build_execution_store()

    assert isinstance(store, InMemoryExecutionStore)


def test_runtime_store_selects_postgres(monkeypatch):
    monkeypatch.setattr(settings, "runtime_backend", "postgres")
    monkeypatch.setattr(settings, "database_url", "postgres://user:pass@localhost/db")

    store = build_execution_store()

    assert isinstance(store, PostgresExecutionStore)


def test_unsupported_runtime_backend_raises(monkeypatch):
    monkeypatch.setattr(settings, "runtime_backend", "not-a-backend")

    with pytest.raises(RuntimeError, match="Unsupported runtime backend"):
        build_execution_store()
