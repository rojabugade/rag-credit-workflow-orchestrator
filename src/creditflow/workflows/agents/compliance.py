from creditflow.workflows.state import UnderwritingState


def compliance_analysis(state: UnderwritingState) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    if state.get("missing_documents"):
        findings.append(
            {
                "code": "POLICY_DOCUMENTATION_INCOMPLETE",
                "category": "INTERNAL_POLICY",
                "status": "OPEN",
                "explanation": (
                    "Illustrative internal policy requires complete evidence before a human decision."
                ),
                "policy_id": "00000000-0000-0000-0000-000000000101",
                "policy_version": state.get("policy_versions", ["synthetic-commercial-v1"])[0],
                "effective_date": "2026-01-01",
                "section": "4.2",
                "source_ids": [],
                "is_external_requirement": False,
            }
        )
    return {"compliance_findings": findings}
