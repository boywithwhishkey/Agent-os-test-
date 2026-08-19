CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE agent_memories
    ALTER COLUMN embedding TYPE vector(64)
    USING embedding::vector(64);

CREATE INDEX IF NOT EXISTS idx_agent_memories_embedding_hnsw
ON agent_memories USING hnsw (embedding vector_cosine_ops)
WHERE embedding IS NOT NULL;
