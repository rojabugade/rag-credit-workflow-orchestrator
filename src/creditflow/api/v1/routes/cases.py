from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, status

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.schemas.underwriting import (
    CaseAssignment,
    CaseCreate,
    CaseHistoryEntry,
    CaseRead,
    CaseUpdate,
    CaseWithdrawal,
)
from creditflow.services.dependencies import RuntimeDep

router = APIRouter(tags=["applications"])


def public_case(item: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "id",
        "tenant_id",
        "borrower_name",
        "requested_amount",
        "currency",
        "jurisdiction",
        "status",
        "version",
        "created_at",
        "updated_at",
        "assigned_analyst",
    }
    return {key: value for key, value in item.items() if key in allowed}


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    principal: PrincipalDep,
    request: Request,
    runtime: RuntimeDep,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=200)],
) -> dict[str, Any]:
    principal.require("analyst", "underwriter")
    item, created = await runtime.create_case(
        principal.tenant_id, principal.subject, data, idempotency_key
    )
    if not created:
        request.state.replayed = True
    return public_case(item)


@router.get("", response_model=dict[str, Any])
async def list_cases(
    principal: PrincipalDep,
    runtime: RuntimeDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    application_status: str | None = Query(default=None, alias="status"),
    assigned_analyst: str | None = Query(default=None),
) -> dict[str, Any]:
    records, total = await runtime.list_cases(
        principal.tenant_id,
        limit=limit,
        offset=offset,
        application_status=application_status,
        assigned_analyst=assigned_analyst,
    )
    return {
        "items": [public_case(item) for item in records],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{case_id}", response_model=CaseRead)
async def get_case(case_id: UUID, principal: PrincipalDep, runtime: RuntimeDep) -> dict[str, Any]:
    return public_case(await runtime.get_case(principal.tenant_id, case_id))


@router.patch("/{case_id}", response_model=CaseRead)
async def update_case(
    case_id: UUID, data: CaseUpdate, principal: PrincipalDep, runtime: RuntimeDep
) -> dict[str, Any]:
    principal.require("analyst", "underwriter")
    return public_case(
        await runtime.update_case(principal.tenant_id, case_id, principal.subject, data)
    )


@router.put("/{case_id}/assignment", response_model=CaseRead)
async def assign_case(
    case_id: UUID, data: CaseAssignment, principal: PrincipalDep, runtime: RuntimeDep
) -> dict[str, Any]:
    principal.require("underwriter", "manager")
    return public_case(
        await runtime.assign_case(principal.tenant_id, case_id, principal.subject, data)
    )


@router.post("/{case_id}/withdraw", response_model=CaseRead)
async def withdraw_case(
    case_id: UUID, data: CaseWithdrawal, principal: PrincipalDep, runtime: RuntimeDep
) -> dict[str, Any]:
    principal.require("analyst", "underwriter")
    return public_case(
        await runtime.withdraw_case(principal.tenant_id, case_id, principal.subject, data)
    )


@router.get("/{case_id}/history", response_model=list[CaseHistoryEntry])
async def get_case_history(
    case_id: UUID, principal: PrincipalDep, runtime: RuntimeDep
) -> list[dict[str, Any]]:
    return await runtime.get_history(principal.tenant_id, case_id)
