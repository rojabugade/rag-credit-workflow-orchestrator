from typing import NotRequired, TypedDict


class UnderwritingState(TypedDict):
    case_id: str
    tenant_id: str
    borrower_name: str
    requested_amount: str
    facts: dict[str, str]
    source_ids: list[str]
    evidence: list[dict[str, object]]
    missing_documents: list[str]
    policy_versions: list[str]
    financial_metrics: NotRequired[list[dict[str, object]]]
    risk_level: NotRequired[str]
    risk_flags: NotRequired[list[dict[str, object]]]
    compliance_findings: NotRequired[list[dict[str, object]]]
    financial_observations: NotRequired[list[str]]
    verification_errors: NotRequired[list[str]]
    correction_attempts: NotRequired[int]
    report: NotRequired[dict[str, object]]
    report_markdown: NotRequired[str]
    review: NotRequired[dict[str, object]]
    status: NotRequired[str]
