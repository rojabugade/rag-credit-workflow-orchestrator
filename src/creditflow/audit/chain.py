import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def create_audit_event(
    *,
    tenant_id: str,
    case_id: str | None,
    actor_id: str,
    event_type: str,
    payload: dict[str, Any],
    previous_hash: str = "0" * 64,
) -> dict[str, Any]:
    event = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "case_id": case_id,
        "actor_id": actor_id,
        "event_type": event_type,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": payload,
        "previous_hash": previous_hash,
    }
    canonical = json.dumps(event, sort_keys=True, separators=(",", ":"), default=str)
    event["event_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    return event


def verify_audit_chain(events: list[dict[str, Any]]) -> bool:
    previous = "0" * 64
    for event in events:
        if event["previous_hash"] != previous:
            return False
        unsigned = {key: value for key, value in event.items() if key != "event_hash"}
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), default=str)
        if hashlib.sha256(canonical.encode()).hexdigest() != event["event_hash"]:
            return False
        previous = event["event_hash"]
    return True
