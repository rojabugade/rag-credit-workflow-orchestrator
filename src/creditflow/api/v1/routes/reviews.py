from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.schemas.underwriting import ReviewRequest
from creditflow.services.dependencies import RuntimeDep

router = APIRouter(prefix="/cases/{case_id}", tags=["reviews and audit"])


@router.post("/review", status_code=status.HTTP_201_CREATED)
async def review_case(
    case_id: UUID, data: ReviewRequest, principal: PrincipalDep, runtime: RuntimeDep
) -> dict[str, Any]:
    principal.require("underwriter", "analyst")
    return await runtime.review(principal.tenant_id, case_id, principal.subject, data)


@router.get("/audit")
async def get_audit(case_id: UUID, principal: PrincipalDep, runtime: RuntimeDep) -> dict[str, Any]:
    events = await runtime.get_audit(principal.tenant_id, case_id)
    return {"items": events, "total": len(events)}
