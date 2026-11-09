from typing import Literal, cast

from creditflow.workflows.state import UnderwritingState


def verify(state: UnderwritingState) -> dict[str, object]:
    valid_sources = set(state.get("source_ids", []))
    cited = {
        source
        for flag in state.get("risk_flags", [])
        for source in cast("list[str]", flag.get("source_ids", []))
    }
    errors = [f"unknown citation: {citation}" for citation in sorted(cited - valid_sources)]
    if not state.get("financial_metrics"):
        errors.append("financial analysis is missing")
    for metric in state.get("financial_metrics", []):
        if metric.get("result") is not None and not metric.get("source_ids"):
            errors.append(f"metric {metric.get('code')} lacks source evidence")
    return {
        "verification_errors": errors,
        "status": "VERIFIED" if not errors else "VERIFICATION_FAILED",
    }


def verification_route(state: UnderwritingState) -> Literal["correct", "generate_report"]:
    return (
        "correct"
        if state.get("verification_errors") and state.get("correction_attempts", 0) < 2
        else "generate_report"
    )


def bounded_correction(state: UnderwritingState) -> dict[str, object]:
    valid = set(state.get("source_ids", []))
    flags = [
        flag
        for flag in state.get("risk_flags", [])
        if set(cast("list[str]", flag.get("source_ids", []))) <= valid
    ]
    return {"risk_flags": flags, "correction_attempts": state.get("correction_attempts", 0) + 1}
