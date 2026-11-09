from datetime import UTC, datetime

from creditflow.schemas.underwriting import Recommendation, RiskLevel, UnderwritingRecommendation
from creditflow.workflows.state import UnderwritingState


def generate_report(state: UnderwritingState) -> dict[str, object]:
    level = RiskLevel(state.get("risk_level", RiskLevel.INSUFFICIENT_DATA.value))
    missing = state.get("missing_documents", [])
    verification_errors = state.get("verification_errors", [])
    recommendation = (
        Recommendation.REQUEST_INFORMATION
        if missing or verification_errors
        else (
            Recommendation.PROCEED_TO_HUMAN_REVIEW
            if level == RiskLevel.LOW
            else Recommendation.MANUAL_REVIEW
        )
    )
    payload = UnderwritingRecommendation(
        case_id=state["case_id"],
        recommendation=recommendation,
        risk_level=RiskLevel.INSUFFICIENT_DATA if verification_errors else level,
        financial_metrics=state.get("financial_metrics", []),
        risk_flags=state.get("risk_flags", []),
        compliance_findings=state.get("compliance_findings", []),
        missing_information=sorted(set(missing + verification_errors)),
        supporting_evidence=state.get("evidence", []),
        narrative=(
            "Automated evidence-backed recommendation for an authorized human underwriter; "
            "not a credit decision."
        ),
        model_provider="deterministic-mock",
        model_version="mock-v1",
        prompt_version="underwriting-v1",
        policy_versions=state.get("policy_versions", []),
        generated_at=datetime.now(UTC),
    )
    metrics = "\n".join(
        f"- **{item.code}**: {item.result or 'unavailable'}" for item in payload.financial_metrics
    )
    report = (
        "# Credit analysis recommendation\n\n> Human decision required.\n\n"
        f"**Risk:** {payload.risk_level}\n\n{payload.narrative}\n\n## Metrics\n{metrics}\n"
    )
    return {
        "report": payload.model_dump(mode="json"),
        "report_markdown": report,
        "status": "AWAITING_HUMAN_REVIEW",
    }
