import {FormEvent, useState} from "react";
import {api} from "../services/api";
import type {CreditCase} from "../types";

export function NewApplication({onCreated}: {onCreated: (item: CreditCase) => Promise<void>}) {
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const submit = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setBusy(true); const form = new FormData(event.currentTarget); try { const item = await api.createCase(String(form.get("borrower")), String(form.get("amount"))); await onCreated(item); setMessage(`Created ${item.borrower_name}.`); event.currentTarget.reset(); } catch (caught) { setMessage(String(caught)); } finally { setBusy(false); } };
  return <><h2>New fictional loan application</h2><form className="panel" onSubmit={submit}><input name="borrower" placeholder="Synthetic legal name" required/><input name="amount" type="number" min="1" step="0.01" placeholder="Requested amount" required/><button disabled={busy}>{busy ? "Creating…" : "Create application"}</button></form>{message && <p>{message}</p>}</>;
}
