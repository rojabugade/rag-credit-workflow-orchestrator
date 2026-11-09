import {FormEvent, useState} from "react";
import {localRoleHeaders} from "../services/api";
import type {CreditCase} from "../types";

export function AIAssistant({selected}: {selected: CreditCase | null}) {
  const [answer, setAnswer] = useState(""), [citations, setCitations] = useState<string[]>([]), [busy, setBusy] = useState(false), [error, setError] = useState("");
  if (!selected) return <><h2>Evidence assistant</h2><p className="empty">Select an application first.</p></>;
  const ask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setAnswer(""); setCitations([]); setError(""); setBusy(true);
    const question = String(new FormData(event.currentTarget).get("question"));
    try {
      const response = await fetch(`/api/v1/applications/${selected.id}/assistant/stream`, {method: "POST", headers: {"Content-Type": "application/json", ...localRoleHeaders()}, body: JSON.stringify({question})});
      if (!response.ok || !response.body) throw new Error(await response.text() || "Assistant stream failed");
      const reader = response.body.getReader(), decoder = new TextDecoder(); let buffer = "";
      while (true) {
        const {done, value} = await reader.read(); if (done) break; buffer += decoder.decode(value, {stream: true});
        const events = buffer.split("\n\n"); buffer = events.pop() ?? "";
        for (const eventText of events) { const line = eventText.split("\n").find(line => line.startsWith("data: ")); if (!line) continue; const event = JSON.parse(line.slice(6)); if (event.type === "token") setAnswer(current => current + event.text); if (event.type === "citations") setCitations(event.source_ids); }
      }
    } catch (caught) { setError(String(caught)); } finally { setBusy(false); }
  };
  return <><h2>Evidence assistant</h2><div className="notice">Read-only, case-scoped, citation-required assistance. It cannot make or execute a lending decision.</div><p>Evidence scope: <b>{selected.borrower_name}</b></p><form className="panel" onSubmit={ask}><textarea name="question" minLength={3} maxLength={2000} placeholder="Ask about the validated recommendation" required/><button disabled={busy}>{busy ? "Streaming…" : "Ask"}</button></form>{error && <div className="error">{error}</div>}{answer && <div className="analysis"><p>{answer}</p><h3>Citations</h3><ul>{citations.map(item => <li key={item}>{item}</li>)}</ul></div>}</>;
}
