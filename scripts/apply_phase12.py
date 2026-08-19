from pathlib import Path

p = Path("app/persistence/postgres_stores.py")
text = p.read_text()

if "async def set_embedding(" not in text:
    marker = "\n\nclass PostgresWorkflowRunStore"
    addition = """
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

        if query.project_id is not None:
            where.append(f"project_id = {bind(query.project_id)}")
        if query.task_id is not None:
            where.append(f"task_id = {bind(query.task_id)}")
        if query.session_id is not None:
            where.append(f"session_id = {bind(query.session_id)}")
        if query.agent is not None:
            where.append(f"agent = {bind(query.agent)}")

        vector_p = bind("[" + ",".join(str(float(v)) for v in vector) + "]")
        limit_p = bind(limit)

        sql = f"SELECT *, (1 - (embedding <=> {vector_p}::vector)) AS semantic_score FROM agent_memories WHERE {' AND '.join(where)} ORDER BY embedding <=> {vector_p}::vector LIMIT {limit_p}"
        rows = await self.db.fetch(sql, *args)
        return [(self._row_to_record(row), float(row.get("semantic_score") or 0.0)) for row in rows]
"""
    if marker not in text:
        raise RuntimeError("PostgresMemoryStore insertion point not found")
    p.write_text(text.replace(marker, addition + marker, 1))

env = Path(".env.example")
text = env.read_text() if env.exists() else ""
for line in [
    "AGENT_OS_EMBEDDING_BACKEND=deterministic",
    "AGENT_OS_EMBEDDING_DIMENSIONS=64",
    "AGENT_OS_SEMANTIC_WEIGHT=0.75",
    "AGENT_OS_LEXICAL_WEIGHT=0.25",
]:
    key = line.split("=", 1)[0] + "="
    if key not in text:
        text += ("\n" if text and not text.endswith("\n") else "") + line + "\n"
env.write_text(text)

print("Phase 12 integration applied.")
