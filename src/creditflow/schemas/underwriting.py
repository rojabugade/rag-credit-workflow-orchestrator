from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field, field_validator

from creditflow.schemas.common import EvidenceRef, StrictModel


class RiskLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class Recommendation(StrEnum):
    PROCEED_TO_HUMAN_REVIEW = "PROCEED_TO_HUMAN_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REQUEST_INFORMATION = "REQUEST_INFORMATION"


class ReviewAction(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVISE = "REVISE"


class MetricResult(StrictModel):
    code: str
    formula: str
    inputs: dict[str, Decimal]
    source_ids: list[str]
    result: Decimal | None
    rounding: str = "ROUND_HALF_EVEN to 4 decimal places"
    validation_status: str
    missing_inputs: list[str] = Field(default_factory=list)


class RiskFlag(StrictModel):
    code: str
    severity: RiskLevel
    reason: str
    rule_version: str
    source_ids: list[str]


class ComplianceFinding(StrictModel):
    code: str
    category: str
    status: str
    explanation: str
    policy_id: UUID
    policy_version: str
    effective_date: date
    section: str
    source_ids: list[str]
    is_external_requirement: bool


class UnderwritingRecommendation(StrictModel):
    schema_version: str = "1.0"
    case_id: UUID
    recommendation: Recommendation
    risk_level: RiskLevel
    financial_metrics: list[MetricResult]
    risk_flags: list[RiskFlag]
    compliance_findings: list[ComplianceFinding]
    missing_information: list[str]
    supporting_evidence: list[EvidenceRef]
    narrative: str
    model_provider: str
    model_version: str
    prompt_version: str
    policy_versions: list[str]
    requires_human_review: bool = True
    generated_at: datetime

    @field_validator("requires_human_review")
    @classmethod
    def must_require_review(cls, value: bool) -> bool:
        if not value:
            raise ValueError("AI recommendations always require authorized human review")
        return value


class CaseCreate(StrictModel):
    borrower_name: str = Field(min_length=1, max_length=200)
    requested_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    jurisdiction: str = Field(default="US", min_length=2, max_length=20)


class CaseRead(CaseCreate):
    id: UUID
    tenant_id: UUID
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    assigned_analyst: str | None = None


class CaseUpdate(StrictModel):
    borrower_name: str | None = Field(default=None, min_length=1, max_length=200)
    requested_amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    jurisdiction: str | None = Field(default=None, min_length=2, max_length=20)
    expected_version: int = Field(ge=1)

    @field_validator("borrower_name", "currency", "jurisdiction")
    @classmethod
    def reject_blank_optional_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("value cannot be blank")
        return value.strip() if value is not None else None


class CaseAssignment(StrictModel):
    analyst_subject: str = Field(min_length=1, max_length=255)
    expected_version: int = Field(ge=1)


class CaseWithdrawal(StrictModel):
    rationale: str = Field(min_length=10, max_length=4000)
    expected_version: int = Field(ge=1)


class CaseHistoryEntry(StrictModel):
    sequence: int
    event_type: str
    actor_id: str
    occurred_at: datetime
    version: int
    changes: dict[str, object]


class ReviewRequest(StrictModel):
    action: ReviewAction
    rationale: str = Field(min_length=10, max_length=4000)
    expected_case_version: int = Field(ge=1)
