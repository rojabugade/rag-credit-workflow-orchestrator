from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from creditflow.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tenants"
    name: Mapped[str] = mapped_column(String(200), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "subject"),)


class UserRole(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_roles"
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40))
    __table_args__ = (UniqueConstraint("user_id", "role"),)


class Borrower(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "borrowers"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    legal_name: Mapped[str] = mapped_column(String(200))
    external_reference: Mapped[str | None] = mapped_column(String(100))


class CreditCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "credit_cases"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    borrower_id: Mapped[UUID] = mapped_column(ForeignKey("borrowers.id"), index=True)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    jurisdiction: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    assigned_analyst: Mapped[str | None] = mapped_column(String(255), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    borrower: Mapped[Borrower] = relationship()
    __mapper_args__ = {"version_id_col": version}


class CaseHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "case_history"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("credit_cases.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    actor_id: Mapped[str] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    case_version: Mapped[int] = mapped_column(Integer)
    changes: Mapped[dict[str, object]] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("case_id", "sequence"),)


class IdempotencyRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "idempotency_records"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    scope: Mapped[str] = mapped_column(String(50))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    resource_id: Mapped[UUID] = mapped_column(Uuid)
    request_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("tenant_id", "scope", "idempotency_key"),)


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), default="UPLOADED")
    visibility: Mapped[str] = mapped_column(String(30), default="CASE")


class DocumentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_versions"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("document_id", "version"),)


class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_chunks"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    citation_id: Mapped[str] = mapped_column(String(300), unique=True)
    page_number: Mapped[int | None] = mapped_column(Integer)
    heading: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    embedding_version: Mapped[str | None] = mapped_column(String(50))
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class FinancialFact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "financial_facts"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    fact_type: Mapped[str] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    period_end: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    source_citation_id: Mapped[str] = mapped_column(String(300))


class FinancialMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "financial_metrics"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    provenance: Mapped[dict[str, object]] = mapped_column(JSON)


class CreditAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "credit_analyses"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    schema_version: Mapped[str] = mapped_column(String(20))
    risk_level: Mapped[str] = mapped_column(String(30))
    recommendation: Mapped[str] = mapped_column(String(50))
    result: Mapped[dict[str, object]] = mapped_column(JSON)
    report_markdown: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))


class RiskFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "risk_findings"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("credit_analyses.id"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(30))
    details: Mapped[dict[str, object]] = mapped_column(JSON)


class PolicyDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "policy_documents"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    policy_version: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(80), index=True)
    jurisdiction: Mapped[str] = mapped_column(String(30), index=True)
    effective_date: Mapped[date] = mapped_column(Date, index=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, index=True)
    is_external_requirement: Mapped[bool] = mapped_column(Boolean, default=False)


class ComplianceFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "compliance_findings"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("credit_analyses.id"), index=True)
    policy_document_id: Mapped[UUID] = mapped_column(ForeignKey("policy_documents.id"))
    code: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict[str, object]] = mapped_column(JSON)


class WorkflowRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "workflow_runs"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    thread_id: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    state_summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class WorkflowCheckpoint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "workflow_checkpoints"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    workflow_run_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_runs.id"), index=True)
    checkpoint_ref: Mapped[str] = mapped_column(String(255))
    state_hash: Mapped[str] = mapped_column(String(64))


class BackgroundJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "background_jobs"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[dict[str, object] | None] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key"),)


class HumanReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "human_reviews"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    reviewer_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(30))
    rationale: Mapped[str] = mapped_column(Text)


class AuditEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "audit_events"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    actor_id: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    previous_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64), unique=True)


class ModelUsageEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "model_usage_events"
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    case_id: Mapped[UUID | None] = mapped_column(ForeignKey("credit_cases.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6))


class EvaluationRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_runs"
    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id"), index=True)
    dataset_version: Mapped[str] = mapped_column(String(50))
    mode: Mapped[str] = mapped_column(String(30))
    metrics: Mapped[dict[str, object]] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean)


Index(
    "ix_credit_cases_tenant_status_created",
    CreditCase.tenant_id,
    CreditCase.status,
    CreditCase.created_at,
)
Index("ix_chunks_tenant_doc_version", DocumentChunk.tenant_id, DocumentChunk.document_version_id)
