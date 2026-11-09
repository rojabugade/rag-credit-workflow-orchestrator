from creditflow.retrieval.models import SearchResult


def reciprocal_rank_fusion(
    result_sets: list[list[SearchResult]], *, k: int = 60, limit: int = 20
) -> list[SearchResult]:
    scores: dict[str, float] = {}
    objects: dict[str, SearchResult] = {}
    for results in result_sets:
        for rank, result in enumerate(results, start=1):
            scores[result.citation_id] = scores.get(result.citation_id, 0.0) + 1 / (k + rank)
            objects[result.citation_id] = result
    ranked = sorted(
        objects.values(), key=lambda result: (-scores[result.citation_id], result.citation_id)
    )
    return [
        SearchResult(item.citation_id, item.text, scores[item.citation_id], item.metadata)
        for item in ranked[:limit]
    ]
