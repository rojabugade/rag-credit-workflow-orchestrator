import {FormEvent, useState} from "react";
import {StatusBadge} from "../components/StatusBadge";
import {api} from "../services/api";
import type {CreditCase} from "../types";

export function DocumentUpload({selected, onRefresh}: {selected: CreditCase | null; onRefresh: () => Promise<void>}) {
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  if (!selected) return <><h2>Document upload</h2><p className="empty">Select an application first.</p></>;
  const upload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement; if (!input.files?.[0]) return;
    setBusy(true); setMessage("");
    try { await api.uploadDocument(selected.id, input.files[0]); setMessage("Document uploaded and evidence indexed for local analysis."); await onRefresh(); event.currentTarget.reset(); }
    catch (caught) { setMessage(String(caught)); } finally { setBusy(false); }
  };
  return <><h2>Document upload</h2><div className="panel"><h3>{selected.borrower_name}</h3><StatusBadge status={selected.status}/><form onSubmit={upload}><label>Supporting PDF, CSV, or DOCX<input name="file" type="file" accept=".pdf,.csv,.docx" required/></label><button disabled={busy}>{busy ? "Uploading…" : "Upload document"}</button></form>{message && <p>{message}</p>}</div></>;
}
