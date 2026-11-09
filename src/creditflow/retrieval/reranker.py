import asyncio
import math
import re
from typing import Protocol

from creditflow.retrieval.models import SearchResult


class Reranker(Protocol):
    async def rerank(
        self, query: str, results: list[SearchResult], *, limit: int
    ) -> list[SearchResult]: ...


def lexical_rerank(
    query: str, results: list[SearchResult], *, limit: int = 6
) -> list[SearchResult]:
    """Deterministic offline fallback; production may inject a cross-encoder."""
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    rescored: list[SearchResult] = []
    for result in results:
        candidate = set(re.findall(r"[a-z0-9]+", result.text.lower()))
        overlap = len(terms & candidate) / math.sqrt(max(1, len(terms) * len(candidate)))
        rescored.append(
            SearchResult(result.citation_id, result.text, result.score + overlap, result.metadata)
        )
    return sorted(rescored, key=lambda result: (-result.score, result.citation_id))[:limit]


class LexicalReranker:
    async def rerank(
        self, query: str, results: list[SearchResult], *, limit: int
    ) -> list[SearchResult]:
        return lexical_rerank(query, results, limit=limit)


class CrossEncoderReranker:
    """Optional production reranker loaded only when the AI dependency extra is installed."""

    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError("install the 'ai' extra to use cross-encoder reranking") from exc
        self._model = CrossEncoder(model)

    async def rerank(
        self, query: str, results: list[SearchResult], *, limit: int
    ) -> list[SearchResult]:
        if not results:
            return []
        scores = await asyncio.to_thread(
            self._model.predict,
            [(query, result.text) for result in results],
        )
        rescored = [
            SearchResult(item.citation_id, item.text, float(score), item.metadata)
            for item, score in zip(results, scores, strict=True)
        ]
        return sorted(rescored, key=lambda item: (-item.score, item.citation_id))[:limit]
