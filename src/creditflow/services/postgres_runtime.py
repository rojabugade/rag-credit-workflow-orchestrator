import hashlib
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from langgraph.types import Command
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from creditflow.audit.chain import create_audit_event
from creditflow.core.config import Settings
from creditflow.core.errors import ConflictError, NotFoundError
from creditflow.db.models.entities import (
    AuditEvent,
    BackgroundJob,
    Borrower,
    CaseHistory,
    CreditAnalysis,
    CreditCase,
    Document,
    DocumentVersion,
    HumanReview,
    IdempotencyRecord,
    User,
)
from creditflow.db.session import session_factory
from creditflow.ingestion.extractors import validate_upload
from creditflow.schemas.underwriting import (
    CaseAssignment,
    CaseCreate,
    CaseUpdate,
    CaseWithdrawal,
    ReviewRequest,
)
from creditflow.services.job_queue import SQSJobQueue
from creditflow.services.object_storage import S3ObjectStorage
from creditflow.workers.sqs_worker import AnalysisMessage, IngestionMessage
from creditflow.workflows.checkpoints import postgres_checkpointer
from creditflow.workflows.graph import build_underwriting_graph


class PostgresRuntime:
    """PostgreSQL/S3/SQS implementation used by deployed API instances."""

    def __init__(self, settings: Settings, storage: S3ObjectStorage, queue: SQSJobQueue) -> None:
        self.settings = settings
        self.storage = storage
        self.queue = queue

    @classmethod
    def from_settings(cls, settings: Settings) -> "PostgresRuntime":
        if not settings.sqs_queue_url:
            raise ValueError("SQS queue URL is required for PostgreSQL runtime")
        return cls(
            settings,
            S3ObjectStorage(
                bucket=settings.s3_bucket,
                region=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
                sse_algorithm=settings.s3_sse_algorithm,
                kms_key_id=settings.s3_kms_key_id,
            ),
            SQSJobQueue(
                settings.sqs_queue_url,
                region=settings.aws_region,
                endpoint_url=settings.sqs_endpoint_url,
            ),
        )

    async def _tenant(self, session: AsyncSession, tenant_id: UUID) -> None:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )

    async def _case_row(
        self, session: AsyncSession, tenant_id: UUID, case_id: UUID, *, lock: bool = False
    ) -> CreditCase:
        statement = select(CreditCase).where(
            CreditCase.id == case_id, CreditCase.tenant_id == tenant_id
        )
        if lock:
            statement = statement.with_for_update()
        row = await session.scalar(statement)
        if row is None:
            raise NotFoundError("application not found")
        return row

    async def _public(self, session: AsyncSession, row: CreditCase) -> dict[str, Any]:
        borrower = await session.scalar(
            select(Borrower).where(
                Borrower.id == row.borrower_id, Borrower.tenant_id == row.tenant_id
            )
        )
        if borrower is None:
            raise NotFoundError("borrower not found")
        return {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "borrower_name": borrower.legal_name,
            "requested_amount": row.requested_amount,
            "currency": row.currency,
            "jurisdiction": row.jurisdiction,
            "status": row.status,
            "version": row.version,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "assigned_analyst": row.assigned_analyst,
        }

    async def _audit(
        self,
        session: AsyncSession,
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

    async def _history(
        self,
        session: AsyncSession,
        row: CreditCase,
        actor: str,
        event_type: str,
        changes: dict[str, Any],
    ) -> None:
        sequence = (
            int(
                await session.scalar(
                    select(func.count())
                    .select_from(CaseHistory)
                    .where(CaseHistory.case_id == row.id)
                )
                or 0
            )
            + 1
        )
        session.add(
            CaseHistory(
                tenant_id=row.tenant_id,
                case_id=row.id,
                sequence=sequence,
                event_type=event_type,
                actor_id=actor,
                occurred_at=datetime.now(UTC),
                case_version=row.version,
                changes=changes,
            )
        )

    async def create_case(
        self, tenant_id: UUID, actor: str, data: CaseCreate, idempotency_key: str
    ) -> tuple[dict[str, Any], bool]:
        request_hash = hashlib.sha256(data.model_dump_json().encode()).hexdigest()
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            existing = await session.scalar(
                select(IdempotencyRecord).where(
                    IdempotencyRecord.tenant_id == tenant_id,
                    IdempotencyRecord.scope == "application.create",
                    IdempotencyRecord.idempotency_key == idempotency_key,
                )
            )
            if existing:
                if existing.request_hash != request_hash:
                    raise ConflictError("idempotency key was reused with a different request")
                row = await self._case_row(session, tenant_id, existing.resource_id)
                return await self._public(session, row), False
            borrower = Borrower(tenant_id=tenant_id, legal_name=data.borrower_name)
            session.add(borrower)
            await session.flush()
            row = CreditCase(
                tenant_id=tenant_id,
                borrower_id=borrower.id,
                requested_amount=data.requested_amount,
                currency=data.currency,
                jurisdiction=data.jurisdiction,
                status="DRAFT",
            )
            session.add(row)
            await session.flush()
            session.add(
                IdempotencyRecord(
                    tenant_id=tenant_id,
                    scope="application.create",
                    idempotency_key=idempotency_key,
                    resource_id=row.id,
                    request_hash=request_hash,
                )
            )
            payload = {"requested_amount": str(data.requested_amount), "currency": data.currency}
            await self._audit(session, tenant_id, row.id, actor, "CASE_CREATED", payload)
            await self._history(session, row, actor, "CASE_CREATED", payload)
            return await self._public(session, row), True

    async def get_case(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            return await self._public(session, await self._case_row(session, tenant_id, case_id))

    async def list_cases(
        self,
        tenant_id: UUID,
        *,
        limit: int,
        offset: int,
        application_status: str | None = None,
        assigned_analyst: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            filters = [CreditCase.tenant_id == tenant_id]
            if application_status:
                filters.append(CreditCase.status == application_status)
            if assigned_analyst:
                filters.append(CreditCase.assigned_analyst == assigned_analyst)
            total = int(
                await session.scalar(select(func.count()).select_from(CreditCase).where(*filters))
                or 0
            )
            rows = list(
                (
                    await session.scalars(
                        select(CreditCase)
                        .where(*filters)
                        .order_by(CreditCase.created_at.desc())
                        .offset(offset)
                        .limit(limit)
                    )
                ).all()
            )
            return [await self._public(session, row) for row in rows], total

    async def update_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseUpdate
    ) -> dict[str, Any]:
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            row = await self._case_row(session, tenant_id, case_id, lock=True)
            if row.status == "WITHDRAWN":
                raise ConflictError("withdrawn applications cannot be updated")
            if row.version != data.expected_version:
                raise ConflictError("application version changed")
            changes = data.model_dump(exclude={"expected_version"}, exclude_none=True)
            if not changes:
                raise ConflictError("at least one application field must change")
            borrower = await session.get(Borrower, row.borrower_id)
            if "borrower_name" in changes and borrower:
                borrower.legal_name = str(changes.pop("borrower_name"))
            for key, value in changes.items():
                setattr(row, key, value)
            await session.flush()
            payload = {
                key: str(value)
                for key, value in data.model_dump(
                    exclude={"expected_version"}, exclude_none=True
                ).items()
            }
            await self._audit(session, tenant_id, case_id, actor, "CASE_UPDATED", payload)
            await self._history(session, row, actor, "CASE_UPDATED", payload)
            return await self._public(session, row)

    async def assign_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseAssignment
    ) -> dict[str, Any]:
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            row = await self._case_row(session, tenant_id, case_id, lock=True)
            if row.version != data.expected_version:
                raise ConflictError("application version changed")
            row.assigned_analyst = data.analyst_subject
            await session.flush()
            payload = {"assigned_analyst": data.analyst_subject}
            await self._audit(session, tenant_id, case_id, actor, "CASE_ASSIGNED", payload)
            await self._history(session, row, actor, "CASE_ASSIGNED", payload)
            return await self._public(session, row)

    async def withdraw_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseWithdrawal
    ) -> dict[str, Any]:
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            row = await self._case_row(session, tenant_id, case_id, lock=True)
            if row.status == "WITHDRAWN":
                return await self._public(session, row)
            if row.version != data.expected_version:
                raise ConflictError("application version changed")
            row.status = "WITHDRAWN"
            await session.flush()
            payload = {"status": "WITHDRAWN", "rationale": data.rationale}
            await self._audit(session, tenant_id, case_id, actor, "CASE_WITHDRAWN", payload)
            await self._history(session, row, actor, "CASE_WITHDRAWN", payload)
            return await self._public(session, row)

    async def get_history(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            await self._case_row(session, tenant_id, case_id)
            rows = list(
                (
                    await session.scalars(
                        select(CaseHistory)
                        .where(CaseHistory.tenant_id == tenant_id, CaseHistory.case_id == case_id)
                        .order_by(CaseHistory.sequence)
                    )
                ).all()
            )
            return [
                {
                    "sequence": r.sequence,
                    "event_type": r.event_type,
                    "actor_id": r.actor_id,
                    "occurred_at": r.occurred_at,
                    "version": r.case_version,
                    "changes": r.changes,
                }
                for r in rows
            ]

    async def add_document(
        self,
        tenant_id: UUID,
        case_id: UUID,
        actor: str,
        filename: str,
        content_type: str,
        content: bytes,
        max_bytes: int,
    ) -> dict[str, Any]:
        checksum = validate_upload(filename, content_type, content, max_bytes)
        document_id, version_id = uuid4(), uuid4()
        object_key = f"tenants/{tenant_id}/applications/{case_id}/documents/{document_id}/v1"
        await self.storage.put(object_key, content, content_type, checksum)
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            await self._case_row(session, tenant_id, case_id, lock=True)
            session.add(
                Document(
                    id=document_id,
                    tenant_id=tenant_id,
                    case_id=case_id,
                    filename=filename,
                    document_type="pending_classification",
                    status="UPLOADED",
                    visibility="CASE",
                )
            )
            session.add(
                DocumentVersion(
                    id=version_id,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    version=1,
                    object_key=object_key,
                    checksum_sha256=checksum,
                    content_type=content_type,
                    size_bytes=len(content),
                )
            )
            payload = {
                "document_id": str(document_id),
                "checksum_sha256": checksum,
                "status": "UPLOADED",
            }
            await self._audit(session, tenant_id, case_id, actor, "DOCUMENT_UPLOADED", payload)
        await self.queue.publish_ingestion(
            IngestionMessage(
                schema_version="1",
                document_id=str(document_id),
                document_version_id=str(version_id),
                case_id=str(case_id),
                tenant_id=str(tenant_id),
                actor=actor,
            )
        )
        return {
            "id": document_id,
            "filename": filename,
            "content_type": content_type,
            "checksum_sha256": checksum,
            "document_type": "pending_classification",
            "issues": [],
            "status": "UPLOADED",
            "version": 1,
        }

    async def list_documents(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            await self._case_row(session, tenant_id, case_id)
            rows = list(
                (
                    await session.scalars(
                        select(Document).where(
                            Document.tenant_id == tenant_id, Document.case_id == case_id
                        )
                    )
                ).all()
            )
            return [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "document_type": r.document_type,
                    "status": r.status,
                    "created_at": r.created_at,
                }
                for r in rows
            ]

    async def start_analysis(
        self, tenant_id: UUID, case_id: UUID, actor: str, idempotency_key: str
    ) -> tuple[dict[str, Any], bool]:
        created = False
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            case = await self._case_row(session, tenant_id, case_id, lock=True)
            existing = await session.scalar(
                select(BackgroundJob).where(
                    BackgroundJob.tenant_id == tenant_id,
                    BackgroundJob.idempotency_key == idempotency_key,
                )
            )
            if existing:
                job = existing
            else:
                job = BackgroundJob(
                    tenant_id=tenant_id,
                    case_id=case_id,
                    idempotency_key=idempotency_key,
                    status="QUEUED",
                    attempts=0,
                )
                session.add(job)
                case.status = "ANALYSIS_QUEUED"
                await session.flush()
                await self._audit(
                    session,
                    tenant_id,
                    case_id,
                    actor,
                    "ANALYSIS_QUEUED",
                    {"job_id": str(job.id)},
                )
                created = True
            result = self._job(job)
        if result["status"] == "QUEUED":
            await self.queue.publish_analysis(
                AnalysisMessage(
                    schema_version="1",
                    job_id=str(result["id"]),
                    case_id=str(case_id),
                    tenant_id=str(tenant_id),
                    idempotency_key=idempotency_key,
                )
            )
        return result, created

    def _job(self, row: BackgroundJob) -> dict[str, Any]:
        return {
            "id": row.id,
            "case_id": row.case_id,
            "tenant_id": row.tenant_id,
            "status": row.status,
            "created_at": row.created_at,
            "error": row.error,
        }

    async def get_job(self, tenant_id: UUID, job_id: UUID) -> dict[str, Any]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            row = await session.scalar(
                select(BackgroundJob).where(
                    BackgroundJob.id == job_id, BackgroundJob.tenant_id == tenant_id
                )
            )
            if row is None:
                raise NotFoundError("job not found")
            return self._job(row)

    async def get_analysis(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            await self._case_row(session, tenant_id, case_id)
            row = await session.scalar(
                select(CreditAnalysis)
                .where(CreditAnalysis.tenant_id == tenant_id, CreditAnalysis.case_id == case_id)
                .order_by(CreditAnalysis.created_at.desc())
                .limit(1)
            )
            if row is None:
                raise NotFoundError("analysis not available")
            return row.result

    async def get_report(self, tenant_id: UUID, case_id: UUID) -> str:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            await self._case_row(session, tenant_id, case_id)
            row = await session.scalar(
                select(CreditAnalysis)
                .where(CreditAnalysis.tenant_id == tenant_id, CreditAnalysis.case_id == case_id)
                .order_by(CreditAnalysis.created_at.desc())
                .limit(1)
            )
            if row is None:
                raise NotFoundError("report not available")
            return row.report_markdown

    async def review(
        self, tenant_id: UUID, case_id: UUID, actor: str, request: ReviewRequest
    ) -> dict[str, Any]:
        if not self.settings.checkpoint_database_url:
            raise ConflictError("durable checkpoint store is unavailable")
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            case = await self._case_row(session, tenant_id, case_id)
            if case.version != request.expected_case_version:
                raise ConflictError("application version changed")
            job = await session.scalar(
                select(BackgroundJob)
                .where(
                    BackgroundJob.tenant_id == tenant_id,
                    BackgroundJob.case_id == case_id,
                    BackgroundJob.status == "AWAITING_HUMAN_REVIEW",
                )
                .order_by(BackgroundJob.created_at.desc())
                .limit(1)
            )
            if job is None:
                raise ConflictError("application has no workflow awaiting review")
        async with postgres_checkpointer(self.settings.checkpoint_database_url) as saver:
            graph = build_underwriting_graph(cast("Any", saver))
            await graph.ainvoke(
                Command(
                    resume={
                        "action": request.action.value,
                        "rationale": request.rationale,
                        "reviewer": actor,
                    }
                ),
                {"configurable": {"thread_id": str(job.id)}},
            )
        async with session_factory.begin() as session:
            await self._tenant(session, tenant_id)
            case = await self._case_row(session, tenant_id, case_id, lock=True)
            job = await session.get(BackgroundJob, job.id)
            user = await session.scalar(
                select(User).where(User.tenant_id == tenant_id, User.subject == actor)
            )
            if user is None:
                raise ConflictError("reviewer is not provisioned")
            session.add(
                HumanReview(
                    tenant_id=tenant_id,
                    case_id=case_id,
                    reviewer_user_id=user.id,
                    action=request.action.value,
                    rationale=request.rationale,
                )
            )
            case.status = f"HUMAN_{request.action.value}"
            if job:
                job.status = "COMPLETED"
            payload = {"action": request.action.value, "rationale": request.rationale}
            await self._audit(session, tenant_id, case_id, actor, "HUMAN_REVIEW_RECORDED", payload)
            return {
                **payload,
                "reviewer": actor,
                "recorded_at": datetime.now(UTC),
                "authorization_checked": True,
            }

    async def get_audit(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]:
        async with session_factory() as session:
            await self._tenant(session, tenant_id)
            await self._case_row(session, tenant_id, case_id)
            rows = list(
                (
                    await session.scalars(
                        select(AuditEvent)
                        .where(AuditEvent.tenant_id == tenant_id, AuditEvent.case_id == case_id)
                        .order_by(AuditEvent.occurred_at)
                    )
                ).all()
            )
            return [
                {
                    "id": r.id,
                    "event_type": r.event_type,
                    "actor_id": r.actor_id,
                    "occurred_at": r.occurred_at,
                    "payload": r.payload,
                    "previous_hash": r.previous_hash,
                    "event_hash": r.event_hash,
                }
                for r in rows
            ]
