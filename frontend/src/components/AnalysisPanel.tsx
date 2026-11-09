import type {UnderwritingAnalysis} from "../types";

export function AnalysisPanel({analysis}: {analysis: UnderwritingAnalysis}) {
  return <div className="analysis">
    <h3>Recommendation: {analysis.recommendation}</h3>
    <div className={`risk ${analysis.risk_level}`}>{analysis.risk_level}</div>
    <p>{analysis.narrative}</p>
    <h3>Financial metrics</h3>
    <table><thead><tr><th>Metric</th><th>Result</th><th>Evidence</th></tr></thead><tbody>
      {analysis.financial_metrics.map(metric => <tr key={metric.code}><td>{metric.code}</td><td>{metric.result ?? "Missing"}</td><td>{metric.source_ids.join(", ") || "None"}</td></tr>)}
    </tbody></table>
    <h3>Risk findings</h3>
    {analysis.risk_flags.length ? analysis.risk_flags.map(flag => <p key={flag.code}><b>{flag.code}</b> — {flag.reason}</p>) : <p>No deterministic risk flags.</p>}
    <h3>Compliance findings</h3>
    {analysis.compliance_findings.length ? analysis.compliance_findings.map(finding => <p key={finding.code}><b>{finding.code}</b> — {finding.explanation}</p>) : <p>No open compliance findings.</p>}
    <h3>Missing information</h3><p>{analysis.missing_information.join(", ") || "None identified"}</p>
    <h3>Supporting evidence</h3><ul>{analysis.supporting_evidence.map(item => <li key={item.source_id}>{item.source_id}</li>)}</ul>
  </div>;
}
