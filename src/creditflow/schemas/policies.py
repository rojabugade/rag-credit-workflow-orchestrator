from datetime import date

from creditflow.schemas.common import StrictModel


class PolicySearchRequest(StrictModel):
    query: str = ""
    effective_on: date = date.max


class PolicyPassageRead(StrictModel):
    citation_id: str
    policy_version: str
    effective_date: date
    is_external_requirement: bool
    text: str


class PolicySearchResponse(StrictModel):
    items: list[PolicyPassageRead]
    total: int
    tenant_id: str
