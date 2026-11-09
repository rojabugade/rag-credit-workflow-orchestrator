from langgraph.types import interrupt

from creditflow.workflows.state import UnderwritingState


def human_review(state: UnderwritingState) -> dict[str, object]:
    decision = interrupt(
        {
            "case_id": state["case_id"],
            "report": state["report"],
            "allowed_actions": ["ACCEPT", "REJECT", "REVISE"],
        }
    )
    return {"review": decision, "status": "REVIEWED"}


def audit_completion(state: UnderwritingState) -> dict[str, object]:
    return {"status": f"HUMAN_{state['review']['action']}"}
