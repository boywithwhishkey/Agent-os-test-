from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.memory.models import MemoryQuery, MemoryRecord, MemoryWrite
from app.memory.store import MemoryStore
from app.models.task import Task
from app.persistence.database import Database
from app.runtime.models import RuntimeExecution
from app.runtime.store import ExecutionStore
from app.services.task_store import TaskStore
from app.workflows.models import WorkflowRun
from app.workflows.store import WorkflowRunStore


def _json(value: Any) -> str:
    return json.dumps(value, default=str, separators=(",", ":"))


def _decode_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


class PostgresMemoryStore(MemoryStore):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def write(self, memory: MemoryWrite) -> MemoryRecord:
        record = MemoryRecord(**memory.model_dump())
        await self.db.execute(
            '''
            INSERT INTO agent_memories (
                id, scope, key, content, project_id, task_id, session_id,
                agent, tags, metadata, importance, created_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::text[],$10::jsonb,$11,$12)
            ''',
            record.id,
            record.scope.value,
            record.key,
            record.content,
            record.project_id,
            record.task_id,
            record.session_id,
            record.agent,
            record.tags,
            _json(record.metadata),
            record.importance,
            record.created_at,
        )
        return record

    async def get(self, memory_id: str) -> MemoryRecord | None:
        row = await self.db.fetchrow(
            "SELECT * FROM agent_memories WHERE id = $1",
            memory_id,
        )
        return self._row_to_record(row) if row else None

    async def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        where: list[str] = []
        args: list[Any] = []

        def bind(value: Any) -> str:
            args.append(value)
            return f"${len(args)}"

        if query.scopes:
            p = bind([scope.value for scope in query.scopes])
            where.append(f"scope = ANY({p}::text[])")
        if query.project_id is not None:
            where.append(f"project_id = {bind(query.project_id)}")
        if query.task_id is not None:
            where.append(f"task_id = {bind(query.task_id)}")
        if query.session_id is not None:
            where.append(f"session_id = {bind(query.session_id)}")
        if query.agent is not None:
            where.append(f"agent = {bind(query.agent)}")
        if query.tags:
            p = bind(query.tags)
            where.append(f"tags && {p}::text[]")
        if query.query:
            p = bind(f"%{query.query}%")
            where.append(f"(key ILIKE {p} OR content ILIKE {p})")

        limit_p = bind(query.limit)
        sql = "SELECT * FROM agent_memories"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY importance DESC, created_at DESC LIMIT {limit_p}"

        rows = await self.db.fetch(sql, *args)
        return [self._row_to_record(row) for row in rows]

    async def delete(self, memory_id: str) -> bool:
        status = await self.db.execute(
            "DELETE FROM agent_memories WHERE id = $1",
            memory_id,
        )
        return status.endswith("1")

    @staticmethod
    def _row_to_record(row: dict[str, Any]) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            scope=row["scope"],
            key=row["key"],
            content=row["content"],
            project_id=row.get("project_id"),
            task_id=row.get("task_id"),
            session_id=row.get("session_id"),
            agent=row.get("agent"),
            tags=list(row.get("tags") or []),
            metadata=_decode_json(row.get("metadata") or {}),
            importance=float(row.get("importance", 0.5)),
            created_at=row["created_at"],
        )

    async def set_embedding(self, memory_id: str, vector: list[float]) -> None:
        literal = "[" + ",".join(str(float(v)) for v in vector) + "]"
        await self.db.execute(
            "UPDATE agent_memories SET embedding = $2::vector WHERE id = $1",
            memory_id,
            literal,
        )

    async def semantic_search(self, *, query: MemoryQuery, vector: list[float], limit: int):
        where = ["embedding IS NOT NULL"]
        args = []

        def bind(value):
            args.append(value)
            return f"${len(args)}"

        if query.scopes:
            p = bind([scope.value for scope in query.scopes])
            where.append(f"scope = ANY({p}::text[])")
        if query.project_id is not None:
            where.append(f"project_id = {bind(query.project_id)}")
        if query.task_id is not None:
            where.append(f"task_id = {bind(query.task_id)}")
        if query.session_id is not None:
            where.append(f"session_id = {bind(query.session_id)}")
        if query.agent is not None:
            where.append(f"agent = {bind(query.agent)}")
        if query.tags:
            p = bind(query.tags)
            where.append(f"tags && {p}::text[]")

        vector_p = bind("[" + ",".join(str(float(v)) for v in vector) + "]")
        limit_p = bind(limit)

        sql = f"SELECT *, (1 - (embedding <=> {vector_p}::vector)) AS semantic_score FROM agent_memories WHERE {' AND '.join(where)} ORDER BY embedding <=> {vector_p}::vector LIMIT {limit_p}"
        rows = await self.db.fetch(sql, *args)
        return [(self._row_to_record(row), float(row.get("semantic_score") or 0.0)) for row in rows]


class PostgresWorkflowRunStore(WorkflowRunStore):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(self, run: WorkflowRun) -> None:
        now = datetime.now(UTC)
        await self.db.execute(
            '''
            INSERT INTO workflow_runs (id, workflow_id, status, payload, updated_at)
            VALUES ($1,$2,$3,$4::jsonb,$5)
            ON CONFLICT (id) DO UPDATE SET
                workflow_id = EXCLUDED.workflow_id,
                status = EXCLUDED.status,
                payload = EXCLUDED.payload,
                updated_at = EXCLUDED.updated_at
            ''',
            run.id,
            run.workflow_id,
            run.status.value,
            _json(run.model_dump(mode="json")),
            now,
        )

    async def get(self, run_id: str) -> WorkflowRun | None:
        row = await self.db.fetchrow(
            "SELECT payload FROM workflow_runs WHERE id = $1",
            run_id,
        )
        if not row:
            return None
        return WorkflowRun.model_validate(_decode_json(row["payload"]))


class PostgresExecutionStore(ExecutionStore):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(self, execution: RuntimeExecution) -> None:
        await self.db.execute(
            '''
            INSERT INTO runtime_executions (
                id, provider, workflow, status, idempotency_key,
                correlation_id, payload, created_at, updated_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9)
            ON CONFLICT (id) DO UPDATE SET
                provider = EXCLUDED.provider,
                workflow = EXCLUDED.workflow,
                status = EXCLUDED.status,
                idempotency_key = EXCLUDED.idempotency_key,
                correlation_id = EXCLUDED.correlation_id,
                payload = EXCLUDED.payload,
                updated_at = EXCLUDED.updated_at
            ''',
            execution.id,
            execution.provider,
            execution.workflow,
            execution.status.value,
            execution.idempotency_key,
            execution.correlation_id,
            _json(execution.model_dump(mode="json")),
            execution.created_at,
            execution.updated_at,
        )

    async def get(self, execution_id: str) -> RuntimeExecution | None:
        row = await self.db.fetchrow(
            "SELECT payload FROM runtime_executions WHERE id = $1",
            execution_id,
        )
        if not row:
            return None
        return RuntimeExecution.model_validate(_decode_json(row["payload"]))

    async def by_idempotency_key(self, key: str) -> RuntimeExecution | None:
        row = await self.db.fetchrow(
            '''
            SELECT payload
            FROM runtime_executions
            WHERE idempotency_key = $1
            ORDER BY updated_at DESC
            LIMIT 1
            ''',
            key,
        )
        if not row:
            return None
        return RuntimeExecution.model_validate(_decode_json(row["payload"]))


class PostgresTaskStore(TaskStore):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(self, task: Task) -> None:
        now = datetime.now(UTC)
        await self.db.execute(
            '''
            INSERT INTO tasks (id, status, payload, created_at, updated_at)
            VALUES ($1,$2,$3::jsonb,$4,$5)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                payload = EXCLUDED.payload,
                updated_at = EXCLUDED.updated_at
            ''',
            task.id,
            task.status.value,
            _json(task.model_dump(mode="json")),
            task.created_at,
            now,
        )

    async def get(self, task_id: str) -> Task | None:
        row = await self.db.fetchrow(
            "SELECT payload FROM tasks WHERE id = $1",
            task_id,
        )
        if not row:
            return None
        return Task.model_validate(_decode_json(row["payload"]))
