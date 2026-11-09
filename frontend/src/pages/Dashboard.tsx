import {Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";
import type {CreditCase} from "../types";

export function Dashboard({cases}: {cases: CreditCase[]}) {
  const awaiting = cases.filter(item => item.status === "AWAITING_HUMAN_REVIEW").length;
  const failed = cases.filter(item => item.status === "ANALYSIS_FAILED").length;
  const chart = [{name: "Total", value: cases.length}, {name: "Human review", value: awaiting}, {name: "Failed", value: failed}];
  return <><h2>Dashboard</h2><p>Operational summary for synthetic underwriting cases.</p><div className="stat-grid"><article><strong>{cases.length}</strong><span>Total applications</span></article><article><strong>{awaiting}</strong><span>Awaiting human review</span></article><article><strong>{failed}</strong><span>Failed analyses</span></article></div><div className="panel" style={{height:260}}><ResponsiveContainer width="100%" height="100%"><BarChart data={chart}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="name"/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="value" fill="#155a91"/></BarChart></ResponsiveContainer></div><div className="notice"><b>Human decision required:</b> AI output is evidence-backed analysis, never a final lending decision.</div></>;
}
