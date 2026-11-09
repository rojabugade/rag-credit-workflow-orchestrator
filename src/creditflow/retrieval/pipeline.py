import asyncio

from creditflow.retrieval.fusion import reciprocal_rank_fusion
from creditflow.retrieval.models import SearchBackend, SearchFilters, SearchResult
from creditflow.retrieval.reranker import LexicalReranker, Reranker


class HybridRetrievalPipeline:
    def __init__(self, backend: SearchBackend, reranker: Reranker | None = None) -> None:
        self.backend = backend
        self.reranker = reranker or LexicalReranker()

    async def search(
        self,
        query: str,
        filters: SearchFilters,
        *,
        candidate_limit: int = 30,
        result_limit: int = 6,
    ) -> list[SearchResult]:
        vector, keyword = await asyncio.gather(
            self.backend.vector_search(query, filters, candidate_limit),
            self.backend.keyword_search(query, filters, candidate_limit),
        )
        fused = reciprocal_rank_fusion([vector, keyword], limit=candidate_limit)
        return await self.reranker.rerank(query, fused, limit=result_limit)


async def hybrid_search(
    backend: SearchBackend,
    query: str,
    filters: SearchFilters,
    *,
    candidate_limit: int = 30,
    result_limit: int = 6,
) -> list[SearchResult]:
    return await HybridRetrievalPipeline(backend).search(
        query,
        filters,
        candidate_limit=candidate_limit,
        result_limit=result_limit,
    )
