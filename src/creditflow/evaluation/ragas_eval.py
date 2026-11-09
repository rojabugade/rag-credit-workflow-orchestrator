from typing import Any


def run_ragas_evaluation(
    rows: list[dict[str, Any]],
    *,
    evaluator_llm: Any,
    evaluator_embeddings: Any,
    provider_backed: bool = False,
) -> dict[str, Any]:
    """Run real RAGAS metrics only after the caller explicitly permits provider calls."""
    if not provider_backed:
        raise ValueError("provider-backed RAGAS evaluation requires explicit approval")
    try:
        from ragas import EvaluationDataset, evaluate
        from ragas.metrics import Faithfulness, LLMContextRecall, ResponseRelevancy
    except ImportError as exc:
        raise RuntimeError("install the 'eval' dependency extra to run RAGAS") from exc
    dataset = EvaluationDataset.from_list(rows)
    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(llm=evaluator_llm),
            ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
            LLMContextRecall(llm=evaluator_llm),
        ],
    )
    return dict(result)
