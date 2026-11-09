from typing import Any, Protocol
from uuid import UUID

from creditflow.schemas.underwriting import (
    CaseAssignment,
    CaseCreate,
    CaseUpdate,
    CaseWithdrawal,
    ReviewRequest,
)


class UnderwritingRuntime(Protocol):
    async def create_case(
        self, tenant_id: UUID, actor: str, data: CaseCreate, idempotency_key: str
    ) -> tuple[dict[str, Any], bool]: ...
    async def get_case(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]: ...
    async def list_cases(
        self,
        tenant_id: UUID,
        *,
        limit: int,
        offset: int,
        application_status: str | None = None,
        assigned_analyst: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]: ...
    async def update_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseUpdate
    ) -> dict[str, Any]: ...
    async def assign_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseAssignment
    ) -> dict[str, Any]: ...
    async def withdraw_case(
        self, tenant_id: UUID, case_id: UUID, actor: str, data: CaseWithdrawal
    ) -> dict[str, Any]: ...
    async def get_history(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]: ...
    async def add_document(
        self,
        tenant_id: UUID,
        case_id: UUID,
        actor: str,
        filename: str,
        content_type: str,
        content: bytes,
        max_bytes: int,
    ) -> dict[str, Any]: ...
    async def list_documents(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]: ...
    async def start_analysis(
        self, tenant_id: UUID, case_id: UUID, actor: str, idempotency_key: str
    ) -> tuple[dict[str, Any], bool]: ...
    async def get_job(self, tenant_id: UUID, job_id: UUID) -> dict[str, Any]: ...
    async def get_analysis(self, tenant_id: UUID, case_id: UUID) -> dict[str, Any]: ...
    async def get_report(self, tenant_id: UUID, case_id: UUID) -> str: ...
    async def review(
        self, tenant_id: UUID, case_id: UUID, actor: str, request: ReviewRequest
    ) -> dict[str, Any]: ...
    async def get_audit(self, tenant_id: UUID, case_id: UUID) -> list[dict[str, Any]]: ...
