import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float


def evaluate_ranking(retrieved: list[str], relevant: set[str], *, k: int) -> RetrievalMetrics:
    ranked = retrieved[:k]
    hits = [1 if item in relevant else 0 for item in ranked]
    precision = sum(hits) / k if k else 0.0
    recall = sum(hits) / len(relevant) if relevant else 0.0
    first = next((index for index, hit in enumerate(hits, start=1) if hit), None)
    reciprocal_rank = 1 / first if first else 0.0
    dcg = sum(hit / math.log2(index + 1) for index, hit in enumerate(hits, start=1))
    ideal_hits = [1] * min(len(relevant), k)
    idcg = sum(hit / math.log2(index + 1) for index, hit in enumerate(ideal_hits, start=1))
    return RetrievalMetrics(precision, recall, reciprocal_rank, dcg / idcg if idcg else 0.0)
