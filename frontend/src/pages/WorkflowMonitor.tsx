import {useEffect, useState} from "react";
import {api} from "../services/api";
import type {AuditEvent, CreditCase} from "../types";

export function WorkflowMonitor({selected}: {selected: CreditCase | null}) {
  const [events, setEvents] = useState<AuditEvent[]>([]), [error, setError] = useState("");
  useEffect(() => { if (selected) void api.getAudit(selected.id).then(setEvents).catch(value => setError(String(value))); }, [selected]);
  if (!selected) return <><h2>Workflow monitor</h2><p className="empty">Select an application first.</p></>;
  return <><h2>Multi-agent workflow monitor</h2><div className="panel"><b>{selected.borrower_name}</b><p>Current durable status: {selected.status}</p></div>{error && <div className="error">{error}</div>}<div className="timeline">{events.filter(item => item.event_type.includes("ANALYSIS") || item.event_type.includes("REVIEW")).map(item => <article key={item.id}><b>{item.event_type}</b><span>{new Date(item.occurred_at).toLocaleString()}</span></article>)}</div></>;
}
