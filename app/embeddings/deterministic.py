import hashlib
import math
from app.embeddings.base import EmbeddingProvider

class DeterministicEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int = 64):
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in " ".join(text.lower().split()).split():
            digest = hashlib.sha256(token.encode()).digest()
            for i in range(self.dimensions):
                b = digest[i % len(digest)]
                vector[i] += (1 if b & 1 else -1) * ((b / 255) + 0.01)
        norm = math.sqrt(sum(v*v for v in vector))
        return [v / norm for v in vector] if norm else vector
