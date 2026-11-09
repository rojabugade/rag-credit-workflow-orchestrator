import hashlib
from typing import Protocol

from openai import AsyncOpenAI

from creditflow.core.errors import ProviderError


class EmbeddingProvider(Protocol):
    model: str
    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class DeterministicEmbeddingProvider:
    """Stable offline embeddings for tests; not intended for relevance quality."""

    model = "deterministic-sha256-v1"
    dimensions = 32

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vectors.append([(byte - 127.5) / 127.5 for byte in digest])
        return vectors


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str, *, model: str, dimensions: int) -> None:
        self.client = AsyncOpenAI(api_key=api_key, max_retries=2, timeout=30)
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
            )
        except Exception as exc:
            raise ProviderError("embedding provider request failed") from exc
        vectors = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
        if any(len(vector) != self.dimensions for vector in vectors):
            raise ProviderError("embedding dimensions did not match configured version")
        return vectors
