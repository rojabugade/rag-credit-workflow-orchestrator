"""Backward-compatible hybrid retrieval exports.

New code should import stage-specific modules or ``HybridRetrievalPipeline``.
"""

from creditflow.retrieval.citations import build_grounded_context, validate_citations
from creditflow.retrieval.fusion import reciprocal_rank_fusion
from creditflow.retrieval.models import SearchBackend, SearchFilters, SearchResult
from creditflow.retrieval.pipeline import HybridRetrievalPipeline, hybrid_search
from creditflow.retrieval.reranker import lexical_rerank

__all__ = [
    "HybridRetrievalPipeline",
    "SearchBackend",
    "SearchFilters",
    "SearchResult",
    "build_grounded_context",
    "hybrid_search",
    "lexical_rerank",
    "reciprocal_rank_fusion",
    "validate_citations",
]
