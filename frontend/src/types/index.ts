export type CaseStatus =
  | "DRAFT"
  | "DOCUMENTS_UPLOADED"
  | "ANALYSIS_QUEUED"
  | "ANALYZING"
  | "AWAITING_HUMAN_REVIEW"
  | "ANALYSIS_FAILED"
  | `HUMAN_${string}`;

export interface CreditCase {
  id: string;
  tenant_id: string;
  borrower_name: string;
  requested_amount: string;
  currency: string;
  jurisdiction: string;
  status: CaseStatus;
  version: number;
  created_at: string;
  updated_at: string;
  assigned_analyst: string | null;
}

export interface FinancialMetric {
  code: string;
  formula: string;
  result: string | null;
  source_ids: string[];
  validation_status: string;
  missing_inputs: string[];
}

export interface UnderwritingAnalysis {
  risk_level: "LOW" | "MODERATE" | "HIGH" | "INSUFFICIENT_DATA";
  recommendation: string;
  financial_metrics: FinancialMetric[];
  risk_flags: Array<{code: string; reason: string; severity: string}>;
  compliance_findings: Array<{code: string; explanation: string; status: string}>;
  missing_information: string[];
  supporting_evidence: Array<{source_id: string}>;
  narrative: string;
}

export interface Job {
  id: string;
  status: string;
  error?: {message: string} | null;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  actor_id: string;
  occurred_at: string;
  event_hash: string;
  payload: Record<string, unknown>;
}

export type PageName =
  | "login"
  | "dashboard"
  | "applications"
  | "new-application"
  | "documents"
  | "analysis"
  | "assistant"
  | "workflow"
  | "report"
  | "reviews"
  | "audit"
  | "evaluation"
  | "monitoring";
