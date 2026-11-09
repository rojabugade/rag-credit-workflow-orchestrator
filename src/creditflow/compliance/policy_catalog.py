from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PolicyPassage:
    citation_id: str
    policy_version: str
    effective_date: date
    is_external_requirement: bool
    text: str


SYNTHETIC_POLICIES = (
    PolicyPassage(
        citation_id="policy-synthetic-v1:section-4.2",
        policy_version="synthetic-commercial-v1",
        effective_date=date(2026, 1, 1),
        is_external_requirement=False,
        text=(
            "Complete financial statements and collateral evidence are required before final "
            "human decision."
        ),
    ),
    PolicyPassage(
        citation_id="policy-synthetic-v2:section-4.2",
        policy_version="synthetic-commercial-v2",
        effective_date=date(2027, 1, 1),
        is_external_requirement=False,
        text="Two comparative annual financial periods are required before final human decision.",
    ),
)


def search_effective_policies(query: str, effective_on: date) -> list[PolicyPassage]:
    normalized = query.strip().lower()
    matches = [
        policy
        for policy in SYNTHETIC_POLICIES
        if policy.effective_date <= effective_on
        and (not normalized or normalized in policy.text.lower())
    ]
    if not matches:
        return []
    newest = max(policy.effective_date for policy in matches)
    return [policy for policy in matches if policy.effective_date == newest]
