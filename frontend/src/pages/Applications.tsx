import {FormEvent, useState} from "react";
import {CaseSelector} from "../components/CaseSelector";
import {api} from "../services/api";
import type {CreditCase} from "../types";

export function Applications({cases, selected, onSelect, onRefresh}: {cases: CreditCase[]; selected: CreditCase | null; onSelect: (item: CreditCase) => void; onRefresh: () => Promise<void>}) {
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const create = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try { const item = await api.createCase(String(form.get("borrower")), String(form.get("amount"))); onSelect(item); await onRefresh(); event.currentTarget.reset(); }
    catch (caught) { setError(String(caught)); } finally { setBusy(false); }
  };
  return <><h2>Applications</h2>{error && <div className="error" role="alert">{error}</div>}<div className="two-column"><form className="panel" onSubmit={create}><h3>Create synthetic case</h3><input name="borrower" placeholder="Synthetic borrower" required/><input name="amount" type="number" min="1" step="0.01" placeholder="Requested amount" required/><button disabled={busy}>{busy ? "Creating…" : "Create case"}</button></form><div><h3>Existing applications</h3><CaseSelector cases={cases} selected={selected} onSelect={onSelect}/></div></div></>;
}
