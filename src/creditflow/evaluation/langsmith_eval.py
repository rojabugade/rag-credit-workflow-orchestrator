from collections.abc import Callable
from typing import Any


def run_langsmith_evaluation(
    target: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    dataset_name: str,
    evaluators: list[Callable[..., Any]],
    experiment_prefix: str,
    enabled: bool = False,
) -> Any:
    """Create a traceable LangSmith experiment without fabricating local scores."""
    if not enabled:
        raise ValueError("LangSmith evaluation is disabled by configuration")
    try:
        from langsmith import evaluate
    except ImportError as exc:
        raise RuntimeError("install the 'eval' dependency extra to run LangSmith") from exc
    return evaluate(
        target,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
        max_concurrency=4,
    )
