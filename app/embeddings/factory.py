from app.core.config import settings
from app.embeddings.deterministic import DeterministicEmbeddingProvider


def build_embedding_provider():
    backend = settings.embedding_backend.lower().strip()
    if backend == "deterministic":
        return DeterministicEmbeddingProvider(settings.embedding_dimensions)
    raise RuntimeError(f"Unsupported embedding backend: {backend}")
