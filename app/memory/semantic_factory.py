from app.core.config import settings
from app.embeddings.factory import build_embedding_provider
from app.memory.factory import build_memory_service
from app.memory.semantic import SemanticMemoryService


def build_semantic_memory_service():
    return SemanticMemoryService(
        build_memory_service(),
        build_embedding_provider(),
        settings.semantic_weight,
        settings.lexical_weight,
    )
