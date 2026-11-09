import {useState} from "react";
import {AnalysisPanel} from "../components/AnalysisPanel";
import {api} from "../services/api";
import type {CreditCase, UnderwritingAnalysis} from "../types";

export function CreditAnalysis({selected, onRefresh}: {selected: CreditCase | null; onRefresh: () => Promise<void>}) {
  const [analysis, setAnalysis] = useState<UnderwritingAnalysis | null>(null), [busy, setBusy] = useState(false), [error, setError] = useState("");
  if (!selected) return <><h2>Credit analysis</h2><p className="empty">Select an application first.</p></>;
  const load = async () => { setBusy(true); setError(""); try { setAnalysis(await api.getAnalysis(selected.id)); } catch (caught) { setError(String(caught)); } finally { setBusy(false); } };
  const analyze = async () => { setBusy(true); setError(""); try { const job = await api.startAnalysis(selected.id); for (let attempt=0; attempt<60; attempt++) { await new Promise(resolve => setTimeout(resolve, 500)); const current = await api.getJob(job.id); if (current.status === "AWAITING_HUMAN_REVIEW") { setAnalysis(await api.getAnalysis(selected.id)); await onRefresh(); return; } if (current.status === "FAILED") throw new Error(current.error?.message ?? "Analysis failed"); } throw new Error("Analysis is still running; check again shortly."); } catch (caught) { setError(String(caught)); } finally { setBusy(false); } };
  return <><h2>Credit analysis</h2><p><b>{selected.borrower_name}</b> — ${Number(selected.requested_amount).toLocaleString()}</p><div className="actions"><button onClick={analyze} disabled={busy}>{busy ? "Analyzing…" : "Start analysis"}</button><button className="secondary" onClick={load} disabled={busy}>Load latest analysis</button></div>{error && <div className="error" role="alert">{error}</div>}{analysis && <AnalysisPanel analysis={analysis}/>}</>;
}
