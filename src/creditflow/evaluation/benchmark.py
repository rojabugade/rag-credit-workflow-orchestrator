import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass

from creditflow.evaluation.retrieval_metrics import evaluate_ranking


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    relevant_citations: frozenset[str]


async def benchmark_retriever(
    name: str,
    cases: list[BenchmarkCase],
    search: Callable[[str], Awaitable[list[str]]],
    *,
    k: int = 6,
) -> dict[str, object]:
    if not cases:
        raise ValueError("benchmark requires at least one labeled case")
    totals = {"precision_at_k": 0.0, "recall_at_k": 0.0, "reciprocal_rank": 0.0, "ndcg_at_k": 0.0}
    latencies: list[float] = []
    for case in cases:
        started = time.perf_counter()
        retrieved = await search(case.query)
        latencies.append((time.perf_counter() - started) * 1000)
        metrics = asdict(evaluate_ranking(retrieved, set(case.relevant_citations), k=k))
        for key, value in metrics.items():
            totals[key] += value
    ordered = sorted(latencies)
    return {
        "name": name,
        "sample_size": len(cases),
        "k": k,
        **{key: value / len(cases) for key, value in totals.items()},
        "latency_ms": {
            "mean": sum(latencies) / len(latencies),
            "p95": ordered[min(len(ordered) - 1, math_index(len(ordered), 0.95))],
        },
    }


def math_index(size: int, percentile: float) -> int:
    return max(0, math_ceil(size * percentile) - 1)


def math_ceil(value: float) -> int:
    integer = int(value)
    return integer if integer == value else integer + 1
