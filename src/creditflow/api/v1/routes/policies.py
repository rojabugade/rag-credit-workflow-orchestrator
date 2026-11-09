from fastapi import APIRouter, status

from creditflow.api.v1.dependencies import PrincipalDep
from creditflow.compliance.policy_catalog import search_effective_policies
from creditflow.schemas.policies import (
    PolicyPassageRead,
    PolicySearchRequest,
    PolicySearchResponse,
)

router = APIRouter(tags=["policies"])


@router.post("/policies/search", response_model=PolicySearchResponse)
async def search_policies(
    query: PolicySearchRequest, principal: PrincipalDep
) -> PolicySearchResponse:
    results = search_effective_policies(query.query, query.effective_on)
    items = [PolicyPassageRead.model_validate(result, from_attributes=True) for result in results]
    return PolicySearchResponse(
        items=items,
        total=len(items),
        tenant_id=str(principal.tenant_id),
    )


@router.post("/admin/policies/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_policy(principal: PrincipalDep) -> dict[str, str]:
    principal.require("policy_admin")
    return {
        "status": "ACCEPTED",
        "message": (
            "Submit policy files through the document ingestion worker in deployed environments."
        ),
    }
