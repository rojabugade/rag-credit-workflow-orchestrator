import {useState} from "react";
import {api} from "../services/api";
import type {AuditEvent, CreditCase} from "../types";

export function ReviewQueue({selected, onRefresh}: {selected: CreditCase | null; onRefresh: () => Promise<void>}) {
  const [audit, setAudit] = useState<AuditEvent[]>([]), [message, setMessage] = useState("");
  if (!selected) return <><h2>Review queue</h2><p className="empty">Select an application first.</p></>;
  const review = async (action: "ACCEPT"|"REJECT"|"REVISE") => { setMessage(""); try { await api.submitReview(selected.id, action, selected.version, `Authorized analyst selected ${action} after reviewing evidence.`); setAudit(await api.getAudit(selected.id)); setMessage(`Review action ${action} recorded.`); await onRefresh(); } catch (caught) { setMessage(String(caught)); } };
  const loadAudit = async () => { try { setAudit(await api.getAudit(selected.id)); } catch (caught) { setMessage(String(caught)); } };
  return <><h2>Review queue</h2><div className="panel"><h3>{selected.borrower_name}</h3><p>Status: {selected.status}</p><div className="actions"><button onClick={() => review("ACCEPT")}>Accept recommendation</button><button onClick={() => review("REVISE")}>Request revision</button><button className="danger" onClick={() => review("REJECT")}>Reject recommendation</button><button className="secondary" onClick={loadAudit}>Open audit history</button></div>{message && <p>{message}</p>}</div>{audit.length>0 && <><h3>Audit history</h3><div className="timeline">{audit.map(event => <article key={event.id}><b>{event.event_type}</b><span>{new Date(event.occurred_at).toLocaleString()} · {event.actor_id}</span><code>{event.event_hash.slice(0,16)}…</code></article>)}</div></>}</>;
}
