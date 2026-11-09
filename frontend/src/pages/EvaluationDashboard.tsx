import {useState} from "react";
import {api} from "../services/api";

export function EvaluationDashboard() {
  const [report, setReport] = useState<Record<string, unknown>|null>(null), [error, setError] = useState("");
  const load = async () => { try { setReport(await api.getLatestEvaluation()); setError(""); } catch (caught) { setError(String(caught)); } };
  return <><h2>AI evaluation dashboard</h2><p>Displays measured synthetic evaluation results only; no scores are fabricated.</p><button onClick={load}>Load latest evaluation</button>{error && <div className="error">{error}</div>}{report && <pre>{JSON.stringify(report, null, 2)}</pre>}</>;
}
