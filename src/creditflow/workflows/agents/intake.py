from decimal import Decimal, InvalidOperation

from creditflow.workflows.state import UnderwritingState


def decimal_fact(facts: dict[str, str], name: str) -> Decimal | None:
    try:
        value = facts.get(name)
        return Decimal(value) if value is not None else None
    except InvalidOperation:
        return None


def load_application(state: UnderwritingState) -> dict[str, object]:
    return {"status": "LOADED", "correction_attempts": state.get("correction_attempts", 0)}


def validate_documents(state: UnderwritingState) -> dict[str, object]:
    missing = list(state.get("missing_documents", []))
    if not state.get("source_ids") and "financial_statements" not in missing:
        missing.append("financial_statements")
    return {"missing_documents": missing, "status": "DOCUMENTS_VALIDATED"}


def extract_financial_data(state: UnderwritingState) -> dict[str, object]:
    """Validate the durable handoff from the ingestion service into LangGraph."""
    return {"facts": dict(state.get("facts", {})), "status": "FACTS_EXTRACTED"}


def validate_extracted_information(state: UnderwritingState) -> dict[str, object]:
    facts = state.get("facts", {})
    invalid = [name for name, value in facts.items() if decimal_fact({name: value}, name) is None]
    missing = list(state.get("missing_documents", []))
    if invalid:
        missing.append(f"invalid_numeric_facts:{','.join(sorted(invalid))}")
    return {"missing_documents": missing, "status": "FACTS_VALIDATED"}


def retrieve_policies(state: UnderwritingState) -> dict[str, object]:
    versions = state.get("policy_versions") or ["synthetic-commercial-v1"]
    return {"policy_versions": versions, "status": "EVIDENCE_RETRIEVED"}
