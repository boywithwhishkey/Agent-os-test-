import os
from app.embeddings.factory import build_embedding_provider
from app.memory.factory import build_memory_service
from app.memory.semantic import SemanticMemoryService

def build_semantic_memory_service():
    return SemanticMemoryService(
        build_memory_service(),
        build_embedding_provider(),
        float(os.getenv("AGENT_OS_SEMANTIC_WEIGHT", "0.75")),
        float(os.getenv("AGENT_OS_LEXICAL_WEIGHT", "0.25")),
    )
