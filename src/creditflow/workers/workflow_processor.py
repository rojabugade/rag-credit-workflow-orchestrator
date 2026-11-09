import hashlib
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, text

from creditflow.audit.chain import create_audit_event
from creditflow.core.config import Settings
from creditflow.db.models.entities import (
    AuditEvent,
    BackgroundJob,
    Borrower,
    CreditAnalysis,
    CreditCase,
    FinancialFact,
)
from creditflow.db.session import session_factory
from creditflow.workers.sqs_worker import AnalysisMessage
from creditflow.workflows.checkpoints import postgres_checkpointer
from creditflow.workflows.graph import build_underwriting_graph


class PostgresWorkflowProcessor:
    """Idempotent SQS handler that persists workflow state and recommendations."""

    def __init__(self, settings: Settings) -> None:
        if not settings.checkpoint_database_url:
            raise ValueError("checkpoint database URL is required by the production worker")
        self.settings = settings

    async def process(self, message: AnalysisMessage) -> None:
        tenant_id, job_id, case_id = (
            UUID(message.tenant_id),
            UUID(message.job_id),
            UUID(message.case_id),
        )
        async with session_factory() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            await session.connection(execution_options={"schema_translate_map": None})
            job = await session.scalar(
                select(BackgroundJob)
                .where(
                    BackgroundJob.id == job_id,
                    BackgroundJob.tenant_id == tenant_id,
                    BackgroundJob.case_id == case_id,
                )
                .with_for_update(skip_locked=True)
            )
            if job is None:
                raise ValueError("background job does not exist for this tenant")
            if job.status in {"AWAITING_HUMAN_REVIEW", "COMPLETED"}:
                return
            job.status = "RUNNING"
            job.attempts += 1
            case_row = await session.scalar(
                select(CreditCase).where(
                    CreditCase.id == case_id, CreditCase.tenant_id == tenant_id
                )
            )
            if case_row is None:
                raise ValueError("credit application does not exist for this tenant")
            borrower = await session.scalar(
                select(Borrower).where(
                    Borrower.id == case_row.borrower_id, Borrower.tenant_id == tenant_id
                )
            )
            if borrower is None:
                raise ValueError("borrower does not exist for this tenant")
            facts = list(
                (
                    await session.scalars(
                        select(FinancialFact).where(
                            FinancialFact.case_id == case_id,
                            FinancialFact.tenant_id == tenant_id,
                        )
                    )
                ).all()
            )
            case_row.status = "ANALYZING"
            await session.commit()

        state = {
            "case_id": str(case_id),
            "tenant_id": str(tenant_id),
            "borrower_name": borrower.legal_name,
            "requested_amount": str(case_row.requested_amount),
            "facts": {fact.fact_type: str(fact.amount) for fact in facts},
            "source_ids": [fact.source_citation_id for fact in facts],
            "evidence": [
                {
                    "source_id": fact.source_citation_id,
                    "document_id": case_id,
                    "version": 1,
                    "excerpt_hash": hashlib.sha256(
                        f"{fact.fact_type}:{fact.amount}".encode()
                    ).hexdigest(),
                }
                for fact in facts
            ],
            "missing_documents": [] if facts else ["financial_statements"],
            "policy_versions": ["synthetic-commercial-v1"],
        }
        config = {"configurable": {"thread_id": str(job_id)}}
        try:
            async with postgres_checkpointer(
                self.settings.checkpoint_database_url or ""
            ) as checkpointer:
                graph = build_underwriting_graph(cast("Any", checkpointer))
                await graph.ainvoke(state, config)
                snapshot = await graph.aget_state(config)
            values = dict(snapshot.values)
            report = cast("dict[str, Any]", values["report"])
            async with session_factory() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(tenant_id)},
                )
                job = await session.get(BackgroundJob, job_id)
                case_row = await session.get(CreditCase, case_id)
                if job is None or case_row is None:
                    raise ValueError("workflow records disappeared during execution")
                session.add(
                    CreditAnalysis(
                        tenant_id=tenant_id,
                        case_id=case_id,
                        schema_version=str(report.get("schema_version", "1.0")),
                        risk_level=str(report["risk_level"]),
                        recommendation=str(report["recommendation"]),
                        result=report,
                        report_markdown=str(values.get("report_markdown", "")),
                        model_version=str(report.get("model_version", "unknown")),
                        prompt_version=str(report.get("prompt_version", "unknown")),
                    )
                )
                job.status = "AWAITING_HUMAN_REVIEW"
                case_row.status = "AWAITING_HUMAN_REVIEW"
                await self._append_audit(
                    session,
                    tenant_id,
                    case_id,
                    "worker",
                    "ANALYSIS_COMPLETED",
                    {"job_id": str(job_id)},
                )
                await session.commit()
        except Exception as exc:
            async with session_factory() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(tenant_id)},
                )
                job = await session.get(BackgroundJob, job_id)
                case_row = await session.get(CreditCase, case_id)
                if job is not None:
                    job.status = "FAILED"
                    job.error = {"type": type(exc).__name__, "message": "workflow execution failed"}
                if case_row is not None:
                    case_row.status = "ANALYSIS_FAILED"
                await session.commit()
            raise

    async def _append_audit(
        self,
        session: Any,
        tenant_id: UUID,
        case_id: UUID,
        actor: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        previous = await session.scalar(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id, AuditEvent.case_id == case_id)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(1)
        )
        event = create_audit_event(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            actor_id=actor,
            event_type=event_type,
            payload=payload,
            previous_hash=previous.event_hash if previous else "0" * 64,
        )
        session.add(
            AuditEvent(
                id=UUID(event["id"]),
                tenant_id=tenant_id,
                case_id=case_id,
                actor_id=actor,
                event_type=event_type,
                occurred_at=datetime.fromisoformat(event["occurred_at"]),
                payload=payload,
                previous_hash=event["previous_hash"],
                event_hash=event["event_hash"],
            )
        )
