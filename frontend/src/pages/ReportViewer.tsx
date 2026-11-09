import {useState} from "react";
import {api} from "../services/api";
import type {CreditCase} from "../types";

export function ReportViewer({selected}: {selected: CreditCase | null}) {
  const [report, setReport] = useState(""), [error, setError] = useState("");
  if (!selected) return <><h2>Underwriting report</h2><p className="empty">Select an application first.</p></>;
  const load = async () => { try { setReport(await api.getReport(selected.id)); setError(""); } catch (caught) { setError(String(caught)); } };
  return <><h2>Underwriting report viewer</h2><button onClick={load}>Load validated report</button>{error && <div className="error">{error}</div>}{report && <pre>{report}</pre>}</>;
}
