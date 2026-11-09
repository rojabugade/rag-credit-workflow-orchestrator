from creditflow.retrieval.hybrid import SearchResult, reciprocal_rank_fusion, validate_citations


def test_hybrid_fusion_rewards_shared_results() -> None:
    shared = SearchResult("shared:p1", "debt coverage", 0.5, {})
    vector = [SearchResult("vector:p1", "similar", 0.9, {}), shared]
    keyword = [shared, SearchResult("keyword:p1", "exact", 0.9, {})]
    fused = reciprocal_rank_fusion([vector, keyword])
    assert fused[0].citation_id == "shared:p1"
    assert validate_citations(["shared:p1", "fake:p9"], fused) == ["fake:p9"]
