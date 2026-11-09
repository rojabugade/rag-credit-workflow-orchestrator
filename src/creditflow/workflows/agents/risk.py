from creditflow.risk.rules import evaluate_rules
from creditflow.schemas.underwriting import MetricResult
from creditflow.workflows.state import UnderwritingState


def risk_analysis(state: UnderwritingState) -> dict[str, object]:
    metrics = [MetricResult.model_validate(item) for item in state.get("financial_metrics", [])]
    level, flags = evaluate_rules(metrics, missing_documents=state.get("missing_documents", []))
    return {
        "risk_level": level.value,
        "risk_flags": [flag.model_dump(mode="json") for flag in flags],
    }
