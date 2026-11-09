from creditflow.audit.chain import create_audit_event, verify_audit_chain


def test_audit_chain_detects_tampering() -> None:
    first = create_audit_event(
        tenant_id="t", case_id="c", actor_id="u", event_type="CREATED", payload={}
    )
    second = create_audit_event(
        tenant_id="t",
        case_id="c",
        actor_id="u",
        event_type="REVIEWED",
        payload={"action": "ACCEPT"},
        previous_hash=first["event_hash"],
    )
    assert verify_audit_chain([first, second])
    second["payload"]["action"] = "REJECT"
    assert not verify_audit_chain([first, second])
