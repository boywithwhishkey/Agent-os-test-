from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Expected Phase 10 content not found in {path}")
    path.write_text(text.replace(old, new, 1))


def append_env(line: str) -> None:
    path = Path(".env.example")
    text = path.read_text() if path.exists() else ""
    key = line.split("=", 1)[0] + "="
    if key not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
        path.write_text(text)


# Memory backend: memory -> PostgreSQL option
memory_factory = Path("app/memory/factory.py")
replace_once(
    memory_factory,
    "from app.memory.in_memory import InMemoryMemoryStore\nfrom app.memory.service import MemoryService",
    "from app.memory.in_memory import InMemoryMemoryStore\n"
    "from app.memory.service import MemoryService\n"
    "from app.persistence.database import AsyncpgDatabase\n"
    "from app.persistence.postgres_stores import PostgresMemoryStore",
)
replace_once(
    memory_factory,
    '''    if backend == "memory":
        return MemoryService(InMemoryMemoryStore())
    # Future adapters:
    # - postgres
    # - postgres_pgvector
    # - redis_cache + postgres
    raise RuntimeError(
        f"Unsupported memory backend: {backend}. "
        "Supported backend for Phase 7: memory."
    )''',
    '''    if backend == "memory":
        return MemoryService(InMemoryMemoryStore())
    if backend in {"postgres", "postgres_pgvector"}:
        return MemoryService(PostgresMemoryStore(AsyncpgDatabase.from_env()))
    raise RuntimeError(
        f"Unsupported memory backend: {backend}. "
        "Supported backends: memory, postgres, postgres_pgvector."
    )''',
)

# Workflow store backend
workflow_factory = Path("app/workflows/factory.py")
replace_once(
    workflow_factory,
    "from __future__ import annotations\n",
    "from __future__ import annotations\n\nimport os\n",
)
replace_once(
    workflow_factory,
    "from app.workflows.store import InMemoryWorkflowRunStore",
    "from app.workflows.store import InMemoryWorkflowRunStore\n"
    "from app.persistence.database import AsyncpgDatabase\n"
    "from app.persistence.postgres_stores import PostgresWorkflowRunStore",
)
replace_once(
    workflow_factory,
    '''def build_workflow_engine() -> WorkflowEngine:
    approvals = ApprovalStore()''',
    '''def build_workflow_engine() -> WorkflowEngine:
    backend = os.getenv("AGENT_OS_WORKFLOW_BACKEND", "memory").lower().strip()
    if backend == "memory":
        store = InMemoryWorkflowRunStore()
    elif backend == "postgres":
        store = PostgresWorkflowRunStore(AsyncpgDatabase.from_env())
    else:
        raise RuntimeError(f"Unsupported workflow backend: {backend}")

    approvals = ApprovalStore()''',
)
replace_once(
    workflow_factory,
    "        store=InMemoryWorkflowRunStore(),",
    "        store=store,",
)

# Runtime execution backend
runtime_factory = Path("app/runtime/factory.py")
replace_once(
    runtime_factory,
    "from app.runtime.store import InMemoryExecutionStore",
    "from app.runtime.store import InMemoryExecutionStore\n"
    "from app.persistence.database import AsyncpgDatabase\n"
    "from app.persistence.postgres_stores import PostgresExecutionStore",
)
replace_once(
    runtime_factory,
    '''def build_runtime() -> IntegrationRuntime:
    registry = ConnectorRegistry()''',
    '''def build_runtime() -> IntegrationRuntime:
    registry = ConnectorRegistry()
    backend = os.getenv("AGENT_OS_RUNTIME_BACKEND", "memory").lower().strip()
    if backend == "memory":
        store = InMemoryExecutionStore()
    elif backend == "postgres":
        store = PostgresExecutionStore(AsyncpgDatabase.from_env())
    else:
        raise RuntimeError(f"Unsupported runtime backend: {backend}")''',
)
replace_once(
    runtime_factory,
    "        store=InMemoryExecutionStore(),",
    "        store=store,",
)

# Add production dependencies without overwriting pyproject.
pyproject = Path("pyproject.toml")
text = pyproject.read_text()
if '"asyncpg>=0.30,<1",' not in text:
    text = text.replace(
        '"httpx>=0.27,<1",\n]',
        '"httpx>=0.27,<1",\n'
        '"asyncpg>=0.30,<1",\n'
        '"redis>=5,<7",\n'
        ']',
        1,
    )
    pyproject.write_text(text)

for line in [
    "DATABASE_URL=postgresql://agent_os:agent_os_dev@localhost:5432/agent_os",
    "REDIS_URL=redis://localhost:6379/0",
    "AGENT_OS_MEMORY_BACKEND=memory",
    "AGENT_OS_WORKFLOW_BACKEND=memory",
    "AGENT_OS_RUNTIME_BACKEND=memory",
    "AGENT_OS_QUEUE_BACKEND=memory",
    "AGENT_OS_QUEUE_PREFIX=agent-os",
    "AGENT_OS_DB_POOL_MIN=1",
    "AGENT_OS_DB_POOL_MAX=10",
    "AGENT_OS_DB_COMMAND_TIMEOUT=30",
]:
    append_env(line)

print("Phase 11 durable-core integration applied.")
