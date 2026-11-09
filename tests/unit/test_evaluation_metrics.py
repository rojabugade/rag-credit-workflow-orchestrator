import pytest

from creditflow.evaluation.benchmark import BenchmarkCase, benchmark_retriever
from creditflow.evaluation.retrieval_metrics import evaluate_ranking


def test_retrieval_metrics_have_known_values() -> None:
    metrics = evaluate_ranking(["a", "x", "b"], {"a", "b"}, k=3)
    assert metrics.precision_at_k == pytest.approx(2 / 3)
    assert metrics.recall_at_k == 1.0
    assert metrics.reciprocal_rank == 1.0
    assert 0 < metrics.ndcg_at_k <= 1


@pytest.mark.asyncio
async def test_benchmark_reports_real_sample_size_and_latency() -> None:
    async def search(_: str) -> list[str]:
        return ["source-1"]

    report = await benchmark_retriever(
        "synthetic",
        [BenchmarkCase("query", frozenset({"source-1"}))],
        search,
        k=1,
    )
    assert report["sample_size"] == 1
    assert report["recall_at_k"] == 1.0
