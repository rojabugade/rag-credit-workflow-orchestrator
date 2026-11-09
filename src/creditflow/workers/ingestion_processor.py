from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, text

from creditflow.audit.chain import create_audit_event
from creditflow.db.models.entities import (
    AuditEvent,
    CreditCase,
    Document,
    DocumentChunk,
    DocumentVersion,
    FinancialFact,
)
from creditflow.db.session import session_factory
from creditflow.ingestion.extractors import (
    chunk_document,
    extract_document_text,
    identify_document_type,
    validate_document_completeness,
)
from creditflow.services.object_storage import ObjectStorage
from creditflow.workers.sqs_worker import IngestionMessage


class PostgresIngestionProcessor:
    def __init__(self, storage: ObjectStorage) -> None:
        self.storage = storage

    async def process(self, message: IngestionMessage) -> None:
        tenant_id, case_id = UUID(message.tenant_id), UUID(message.case_id)
        document_id, version_id = UUID(message.document_id), UUID(message.document_version_id)
        async with session_factory.begin() as session:
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
            document = await session.scalar(
                select(Document)
                .where(Document.id == document_id, Document.tenant_id == tenant_id)
                .with_for_update(skip_locked=True)
            )
            version = await session.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.id == version_id,
                    DocumentVersion.tenant_id == tenant_id,
                    DocumentVersion.document_id == document_id,
                )
            )
            if document is None or version is None:
                raise ValueError("document ingestion records do not exist")
            if document.status == "PROCESSED":
                return
            document.status = "PROCESSING"
            object_key, content_type = version.object_key, version.content_type

        try:
            content = await self.storage.get(object_key)
            pages = extract_document_text(content, content_type)
            chunks = chunk_document(str(document_id), pages)
            document_type = identify_document_type("\n".join(page.text for page in pages))
            issues = validate_document_completeness(pages)
            async with session_factory.begin() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(tenant_id)},
                )
                document = await session.get(Document, document_id)
                case = await session.get(CreditCase, case_id)
                if document is None or case is None:
                    raise ValueError("document or application disappeared during ingestion")
                for chunk in chunks:
                    session.add(
                        DocumentChunk(
                            tenant_id=tenant_id,
                            document_version_id=version_id,
                            citation_id=str(chunk["citation_id"]),
                            page_number=cast("int", chunk["page"]),
                            heading=None,
                            content=str(chunk["text"]),
                            content_hash=str(chunk["content_hash"]),
                            metadata_json={"case_id": str(case_id), "issues": issues},
                        )
                    )
                if content_type == "text/csv" and chunks:
                    self._financial_facts(
                        session, tenant_id, case, pages[0].text, str(chunks[0]["citation_id"])
                    )
                document.document_type = document_type
                document.status = "PROCESSED"
                case.status = "DOCUMENTS_UPLOADED"
                await self._audit(
                    session,
                    tenant_id,
                    case_id,
                    message.actor,
                    "DOCUMENT_PROCESSED",
                    {
                        "document_id": str(document_id),
                        "document_type": document_type,
                        "issues": issues,
                    },
                )
        except Exception:
            async with session_factory.begin() as session:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                    {"tenant_id": str(tenant_id)},
                )
                document = await session.get(Document, document_id)
                if document is not None:
                    document.status = "FAILED"
            raise

    def _financial_facts(
        self,
        session: Any,
        tenant_id: UUID,
        case: CreditCase,
        extracted: str,
        citation_id: str,
    ) -> None:
        for line in extracted.splitlines()[1:]:
            cells = [cell.strip() for cell in line.split("|")]
            try:
                if len(cells) >= 2 and cells[0]:
                    session.add(
                        FinancialFact(
                            tenant_id=tenant_id,
                            case_id=case.id,
                            fact_type=cells[0],
                            amount=Decimal(cells[1].replace(",", "")),
                            currency=case.currency,
                            source_citation_id=citation_id,
                        )
                    )
            except InvalidOperation:
                continue

    async def _audit(
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
