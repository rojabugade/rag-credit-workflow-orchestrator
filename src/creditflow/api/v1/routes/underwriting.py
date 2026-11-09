from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, status
from fastapi.responses import PlainTextResponse

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.services.dependencies import RuntimeDep

router = APIRouter(tags=["underwriting"])


@router.post("/cases/{case_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_case(
    case_id: UUID,
    principal: PrincipalDep,
    runtime: RuntimeDep,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=200)],
) -> dict[str, Any]:
    principal.require("analyst", "underwriter")
    job, _ = await runtime.start_analysis(
        principal.tenant_id, case_id, principal.subject, idempotency_key
    )
    return job


@router.get("/jobs/{job_id}")
async def get_job(job_id: UUID, principal: PrincipalDep, runtime: RuntimeDep) -> dict[str, Any]:
    return await runtime.get_job(principal.tenant_id, job_id)


@router.get("/cases/{case_id}/analysis")
async def get_analysis(
    case_id: UUID, principal: PrincipalDep, runtime: RuntimeDep
) -> dict[str, Any]:
    return await runtime.get_analysis(principal.tenant_id, case_id)


@router.get("/cases/{case_id}/report", response_class=PlainTextResponse)
async def get_report(case_id: UUID, principal: PrincipalDep, runtime: RuntimeDep) -> str:
    return await runtime.get_report(principal.tenant_id, case_id)
