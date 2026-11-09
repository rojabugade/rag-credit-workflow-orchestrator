import {useEffect, useState} from "react";
import {api} from "../services/api";
import type {AuditEvent, CreditCase} from "../types";

export function AuditTrail({selected}: {selected: CreditCase | null}) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  useEffect(() => { if (selected) void api.getAudit(selected.id).then(setEvents); }, [selected]);
  return <><h2>Audit trail</h2>{!selected ? <p className="empty">Select an application first.</p> : <table><thead><tr><th>Time</th><th>Event</th><th>Actor</th><th>Hash</th></tr></thead><tbody>{events.map(item => <tr key={item.id}><td>{new Date(item.occurred_at).toLocaleString()}</td><td>{item.event_type}</td><td>{item.actor_id}</td><td><code>{item.event_hash.slice(0,16)}…</code></td></tr>)}</tbody></table>}</>;
}
