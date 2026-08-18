CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS agent_memories (
    id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    content TEXT NOT NULL,
    project_id TEXT NULL,
    task_id TEXT NULL,
    session_id TEXT NULL,
    agent TEXT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    importance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    embedding vector NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_memories_scope
    ON agent_memories(scope);
CREATE INDEX IF NOT EXISTS idx_agent_memories_project
    ON agent_memories(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_task
    ON agent_memories(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_session
    ON agent_memories(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_tags
    ON agent_memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_agent_memories_search
    ON agent_memories USING GIN(
        to_tsvector('simple', coalesce(key, '') || ' ' || coalesce(content, ''))
    );

CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow
    ON workflow_runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status
    ON workflow_runs(status);

CREATE TABLE IF NOT EXISTS runtime_executions (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    workflow TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NULL,
    correlation_id TEXT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_runtime_idempotency
    ON runtime_executions(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_runtime_correlation
    ON runtime_executions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_runtime_status
    ON runtime_executions(status);
