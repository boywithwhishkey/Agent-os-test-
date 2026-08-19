import os
from app.embeddings.deterministic import DeterministicEmbeddingProvider

def build_embedding_provider():
    backend = os.getenv("AGENT_OS_EMBEDDING_BACKEND", "deterministic").lower().strip()
    if backend == "deterministic":
        return DeterministicEmbeddingProvider(
            int(os.getenv("AGENT_OS_EMBEDDING_DIMENSIONS", "64"))
        )
    raise RuntimeError(f"Unsupported embedding backend: {backend}")
