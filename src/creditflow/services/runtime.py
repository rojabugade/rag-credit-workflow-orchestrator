import asyncio
import hashlib
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast
from uuid import UUID, uuid4

from langgraph.types import Command

from creditflow.audit.chain import create_audit_event
from creditflow.core.errors import ConflictError, NotFoundError
from creditflow.ingestion.extractors import (
    chunk_document,
    extract_document_text,
    identify_document_type,
    validate_document_completeness,
    validate_upload,
)
from creditflow.schemas.underwriting import (
    CaseAssignment,
    CaseCreate,
    CaseUpdate,
    CaseWithdrawal,
    ReviewRequest,
)
from creditflow.workflows.graph import build_underwriting_graph


class LocalRuntime:
    """Concurrency-safe local runtime; production workers persist the same contracts in PostgreSQL/S3/SQS."""

    def __init__(self) -> None:
        self.cases: dict[UUID, dict[str, Any]] = {}
        self.documents: dict[UUID, list[dict[str, Any]]] = {}
        self.jobs: dict[UUID, dict[str, Any]] = {}
        self.audits: dict[UUID, list[dict[str, Any]]] = {}
        self.case_history: dict[UUID, list[dict[str, Any]]] = {}
        self.tool_logs: list[dict[str, Any]] = []
        self.idempotency: dict[tuple[UUID, str], UUID] = {}
        self.graph = build_underwriting_graph()
        self._lock = asyncio.Lock()

    def _case(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]:
        case = self.cases.get(case_id)
        if case is None or case["tenant_id"] != tenant_id:
            raise NotFoundError("case not found")
        return case

    async def get_case(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]:
        return self._case(tenant_id, case_id)

    async def list_cases(
        self,
        tenant_id: UUID,
        *,
        limit: int,
        offset: int,
        application_status: str | None = None,
        assigned_analyst: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        items = [
            item
            for item in self.cases.values()
            if item["tenant_id"] == tenant_id
            and (application_status is None or item["status"] == application_status)
            and (assigned_analyst is None or item.get("assigned_analyst") == assigned_analyst)
        ]
        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items[offset : offset + limit], len(items)

    async def list_documents(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]:
        self._case(tenant_id, case_id)
        return [
            {key: value for key, value in item.items() if key != "chunks"}
            for item in self.documents.get(case_id, [])
        ]

    async def get_job(self, tenant_id: UUID, job_id: UUID) -> dict[str, Any]:
        job = self.jobs.get(job_id)
        if not job or job["tenant_id"] != tenant_id:
            raise NotFoundError("job not found")
        return job

    async def get_analysis(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]:
        case = self._case(tenant_id, case_id)
        if not case.get("analysis"):
            raise NotFoundError("analysis not available")
        return cast("dict[str, Any]", case["analysis"])

    async def get_report(self, tenant_id: UUID, case_id: UUID) -> str:
        case = self._case(tenant_id, case_id)
        if not case.get("report_markdown"):
            raise NotFoundError("report not available")
        return str(case["report_markdown"])

    async def get_audit(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]:
        self._case(tenant_id, case_id)
        return self.audits.get(case_id, [])

    async def get_history(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]:
        self._case(tenant_id, case_id)
        return self.case_history.get(case_id, [])

    def _audit(
        self, tenant_id: UUID, case_id: UUID, actor: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        events = self.audits.setdefault(case_id, [])
        events.append(
            create_audit_event(
                tenant_id=str(tenant_id),
                case_id=str(case_id),
                actor_id=actor,
                event_type=event_type,
                payload=payload,
                previous_hash=events[-1]["event_hash"] if events else "0" * 64,
            )
        )

    def _history(
        self,
        case: dict[str, Any],
        actor: str,
        event_type: str,
        changes: dict[str, object],
    ) -> None:
        entries = self.case_history.setdefault(case["id"], [])
        entries.append(
            {
                "sequence": len(entries) + 1,
                "event_type": event_type,
                "actor_id": actor,
                "occurred_at": datetime.now(UTC),
                "version": case["version"],
                "changes": changes,
            }
        )

    async def create_case(
        self, tenant_id: UUID, actor: str, data: CaseCreate, idempotency_key: str
    ) -> tuple[dict[str, Any], bool]:
        async with self._lock:
            existing = self.idempotency.get((tenant_id, idempotency_key))
            if existing:
                return self._case(tenant_id, existing), False
            case_id = uuid4()
            now = datetime.now(UTC)
            item = {
                "id": case_id,
                "tenant_id": tenant_id,
                **data.model_dump(),
                "status": "DRAFT",
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "assigned_analyst": None,
                "facts": {},
                "source_ids": [],
                "evidence": [],
                "missing_documents": [],
            }
            self.cases[case_id] = item
            self.idempotency[(tenant_id, idempotency_key)] = case_id
            self._audit(
                tenant_id,
                case_id,
                actor,
                "CASE_CREATED",
                {"requested_amount": str(data.requested_amount), "currency": data.currency},
            )
            self._history(
                item,
                actor,
                "CASE_CREATED",
                {"status": "DRAFT", "borrower_name": data.borrower_name},
            )
            return item, True

    async def update_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseUpdate
    ) -> dict[str, Any]:
        async with self._lock:
            case = self._case(tenant_id, case_id)
            if case["status"] == "WITHDRAWN":
                raise ConflictError("withdrawn applications cannot be updated")
            if case["version"] != data.expected_version:
                raise ConflictError("case version changed; refresh before updating")
            changes = data.model_dump(exclude={"expected_version"}, exclude_none=True)
            if not changes:
                raise ConflictError("at least one application field must change")
            previous = {key: case[key] for key in changes}
            case.update(changes)
            case["version"] += 1
            case["updated_at"] = datetime.now(UTC)
            history_changes: dict[str, object] = {
                key: {"from": str(previous[key]), "to": str(value)}
                for key, value in changes.items()
            }
            self._audit(tenant_id, case_id, actor, "CASE_UPDATED", history_changes)
            self._history(case, actor, "CASE_UPDATED", history_changes)
            return case

    async def assign_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseAssignment
    ) -> dict[str, Any]:
        async with self._lock:
            case = self._case(tenant_id, case_id)
            if case["status"] == "WITHDRAWN":
                raise ConflictError("withdrawn applications cannot be assigned")
            if case["version"] != data.expected_version:
                raise ConflictError("case version changed; refresh before assigning")
            previous = case.get("assigned_analyst")
            case["assigned_analyst"] = data.analyst_subject
            case["version"] += 1
            case["updated_at"] = datetime.now(UTC)
            changes: dict[str, object] = {
                "assigned_analyst": {
                    "from": previous,
                    "to": data.analyst_subject,
                }
            }
            self._audit(tenant_id, case_id, actor, "CASE_ASSIGNED", changes)
            self._history(case, actor, "CASE_ASSIGNED", changes)
            return case

    async def withdraw_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseWithdrawal
    ) -> dict[str, Any]:
        async with self._lock:
            case = self._case(tenant_id, case_id)
            if case["status"] == "WITHDRAWN":
                return case
            if case["version"] != data.expected_version:
                raise ConflictError("case version changed; refresh before withdrawing")
            previous = str(case["status"])
            case["status"] = "WITHDRAWN"
            case["version"] += 1
            case["updated_at"] = datetime.now(UTC)
            changes: dict[str, object] = {
                "status": {"from": previous, "to": "WITHDRAWN"},
                "rationale": data.rationale,
            }
            self._audit(tenant_id, case_id, actor, "CASE_WITHDRAWN", changes)
            self._history(case, actor, "CASE_WITHDRAWN", changes)
            return case

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
        case = self._case(tenant_id, case_id)
        checksum = validate_upload(filename, content_type, content, max_bytes)
        pages = extract_document_text(content, content_type)
        document_id = uuid4()
        chunks = chunk_document(str(document_id), pages)
        item = {
            "id": document_id,
            "filename": filename,
            "content_type": content_type,
            "checksum_sha256": checksum,
            "document_type": identify_document_type("\n".join(p.text for p in pages)),
            "issues": validate_document_completeness(pages),
            "version": 1,
            "chunks": chunks,
        }
        self.documents.setdefault(case_id, []).append(item)
        for chunk in chunks:
            case["source_ids"].append(chunk["citation_id"])
            case["evidence"].append(
                {
                    "source_id": chunk["citation_id"],
                    "document_id": document_id,
                    "version": 1,
                    "excerpt_hash": chunk["content_hash"],
                    "page": chunk["page"],
                    "heading": None,
                }
            )
        if content_type == "text/csv":
            for line in pages[0].text.splitlines()[1:]:
                cells = [cell.strip() for cell in line.split("|")]
                if len(cells) >= 2 and cells[0]:
                    try:
                        case["facts"][cells[0]] = str(Decimal(cells[1].replace(",", "")))
                    except InvalidOperation:
                        continue
        case["version"] += 1
        case["updated_at"] = datetime.now(UTC)
        case["status"] = "DOCUMENTS_UPLOADED"
        self._audit(
            tenant_id,
            case_id,
            actor,
            "DOCUMENT_UPLOADED",
            {
                "document_id": str(document_id),
                "checksum_sha256": checksum,
                "document_type": item["document_type"],
            },
        )
        return {key: value for key, value in item.items() if key != "chunks"}

    async def start_analysis(
        self, tenant_id: UUID, case_id: UUID, actor: str, idempotency_key: str
    ) -> tuple[dict[str, Any], bool]:
        case = self._case(tenant_id, case_id)
        existing_id = self.idempotency.get((tenant_id, f"analyze:{idempotency_key}"))
        if existing_id:
            return self.jobs[existing_id], False
        job_id = uuid4()
        job = {
            "id": job_id,
            "case_id": case_id,
            "tenant_id": tenant_id,
            "status": "QUEUED",
            "thread_id": str(job_id),
            "created_at": datetime.now(UTC),
            "error": None,
        }
        self.jobs[job_id] = job
        self.idempotency[(tenant_id, f"analyze:{idempotency_key}")] = job_id
        case["status"] = "ANALYSIS_QUEUED"
        case["updated_at"] = datetime.now(UTC)
        self._audit(tenant_id, case_id, actor, "ANALYSIS_QUEUED", {"job_id": str(job_id)})
        asyncio.create_task(self._run_job(job_id, actor))
        return job, True

    async def _run_job(self, job_id: UUID, actor: str) -> None:
        job = self.jobs[job_id]
        case = self.cases[job["case_id"]]
        job["status"] = "RUNNING"
        case["status"] = "ANALYZING"
        state = {
            "case_id": str(case["id"]),
            "tenant_id": str(case["tenant_id"]),
            "borrower_name": case["borrower_name"],
            "requested_amount": str(case["requested_amount"]),
            "facts": case["facts"],
            "source_ids": case["source_ids"],
            "evidence": case["evidence"],
            "missing_documents": case["missing_documents"],
            "policy_versions": ["synthetic-commercial-v1"],
        }
        config = {"configurable": {"thread_id": job["thread_id"]}}
        try:
            await self.graph.ainvoke(state, config)
            snapshot = await self.graph.aget_state(config)
            values = dict(snapshot.values)
            case["analysis"] = values.get("report")
            case["report_markdown"] = values.get("report_markdown")
            case["status"] = "AWAITING_HUMAN_REVIEW"
            case["version"] += 1
            case["updated_at"] = datetime.now(UTC)
            job["status"] = "AWAITING_HUMAN_REVIEW"
            self._audit(
                case["tenant_id"],
                case["id"],
                actor,
                "ANALYSIS_COMPLETED",
                {
                    "job_id": str(job_id),
                    "recommendation_hash": hashlib.sha256(
                        str(case["analysis"]).encode()
                    ).hexdigest(),
                },
            )
        except Exception as exc:
            job["status"] = "FAILED"
            job["error"] = {"type": type(exc).__name__, "message": "workflow execution failed"}
            case["status"] = "ANALYSIS_FAILED"
            self._audit(
                case["tenant_id"],
                case["id"],
                "worker",
                "ANALYSIS_FAILED",
                {"job_id": str(job_id), "error_type": type(exc).__name__},
            )

    async def review(
        self, tenant_id: UUID, case_id: UUID, actor: str, request: ReviewRequest
    ) -> dict[str, Any]:
        case = self._case(tenant_id, case_id)
        if case["version"] != request.expected_case_version:
            raise ConflictError("case version changed; refresh before reviewing")
        actor_roles_checked_externally = True
        job = next(
            (
                item
                for item in self.jobs.values()
                if item["case_id"] == case_id and item["status"] == "AWAITING_HUMAN_REVIEW"
            ),
            None,
        )
        if not job:
            raise ConflictError("case has no workflow awaiting review")
        config = {"configurable": {"thread_id": job["thread_id"]}}
        await self.graph.ainvoke(
            Command(
                resume={
                    "action": request.action.value,
                    "rationale": request.rationale,
                    "reviewer": actor,
                }
            ),
            config,
        )
        case["status"] = f"HUMAN_{request.action.value}"
        case["version"] += 1
        case["updated_at"] = datetime.now(UTC)
        job["status"] = "COMPLETED"
        review = {
            "action": request.action.value,
            "rationale": request.rationale,
            "reviewer": actor,
            "recorded_at": datetime.now(UTC),
            "authorization_checked": actor_roles_checked_externally,
        }
        case["review"] = review
        self._audit(
            tenant_id,
            case_id,
            actor,
            "HUMAN_REVIEW_RECORDED",
            {"action": request.action.value, "rationale": request.rationale},
        )
        self._history(
            case,
            actor,
            "HUMAN_REVIEW_RECORDED",
            {"action": request.action.value, "rationale": request.rationale},
        )
        return review


runtime = LocalRuntime()
