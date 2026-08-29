from dataclasses import dataclass

from app.memory.models import MemoryContext, MemoryQuery, MemoryRecord, MemoryWrite


@dataclass(slots=True)
class RankedMemory:
    record: MemoryRecord
    score: float
    semantic_score: float = 0.0
    lexical_score: float = 0.0

class SemanticMemoryService:
    def __init__(self, memory, embeddings, semantic_weight=0.75, lexical_weight=0.25):
        total = semantic_weight + lexical_weight
        self.memory = memory
        self.embeddings = embeddings
        self.semantic_weight = semantic_weight / total
        self.lexical_weight = lexical_weight / total

    @property
    def store(self):
        return self.memory.store

    async def remember(self, memory: MemoryWrite):
        record = await self.memory.remember(memory)
        if hasattr(self.memory.store, "set_embedding"):
            vector = await self.embeddings.embed(f"{record.key}\n{record.content}")
            await self.memory.store.set_embedding(record.id, vector)
        return record

    async def hybrid_recall(self, query: MemoryQuery):
        semantic = []
        if query.query and hasattr(self.memory.store, "semantic_search"):
            vector = await self.embeddings.embed(query.query)
            semantic = await self.memory.store.semantic_search(
                query=query, vector=vector, limit=max(query.limit * 3, query.limit)
            )

        lexical_query = query.model_copy(update={"limit": max(query.limit * 3, query.limit)})
        lexical = await self.memory.recall(lexical_query)

        terms = set((query.query or "").lower().split())
        lexical_scores = {}
        for record in lexical:
            haystack = f"{record.key} {record.content}".lower()
            lexical_scores[record.id] = (
                sum(term in haystack for term in terms) / len(terms) if terms else 0.0
            )

        semantic_scores = {r.id: s for r, s in semantic}
        records = {r.id: r for r in lexical}
        records.update({r.id: r for r, _ in semantic})

        ranked = []
        for record in records.values():
            ss = semantic_scores.get(record.id, 0.0)
            ls = lexical_scores.get(record.id, 0.0)
            score = self.semantic_weight * ss + self.lexical_weight * ls + 0.05 * float(record.importance)
            ranked.append(RankedMemory(record, score, ss, ls))

        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked[:query.limit]

    async def recall(self, query: MemoryQuery):
        return [
            item.record.model_copy(
                update={
                    "score": item.score,
                    "semantic_score": item.semantic_score,
                    "lexical_score": item.lexical_score,
                }
            )
            for item in await self.hybrid_recall(query)
        ]

    async def build_context(self, query: MemoryQuery, max_characters=6000) -> MemoryContext:
        ranked = await self.hybrid_recall(query)
        rendered = compress_ranked_memories(ranked, max_characters=max_characters)
        return MemoryContext(records=[item.record for item in ranked], rendered=rendered)

def compress_ranked_memories(ranked, max_characters=6000):
    lines, used = [], 0
    for item in ranked:
        line = f"[{item.record.scope.value}:{item.record.key} score={item.score:.3f}] {item.record.content}"
        extra = len(line) + (1 if lines else 0)
        if used + extra > max_characters:
            remaining = max_characters - used - (1 if lines else 0)
            if remaining > 20:
                lines.append(line[:remaining])
            break
        lines.append(line)
        used += extra
    return "\n".join(lines)
