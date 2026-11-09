import type {AuditEvent, CreditCase, Job, UnderwritingAnalysis} from "../types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-Local-Roles", localStorage.getItem("creditrisk.roles") ?? "analyst,policy_admin");
  const response = await fetch(url, {...init, headers});
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed (${response.status})`);
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  async listCases(): Promise<CreditCase[]> {
    return (await request<{items: CreditCase[]}>("/api/v1/applications")).items;
  },
  getCase: (id: string) => request<CreditCase>(`/api/v1/applications/${id}`),
  createCase: (borrowerName: string, amount: string) =>
    request<CreditCase>("/api/v1/applications", {
      method: "POST",
      headers: {"Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID()},
      body: JSON.stringify({
        borrower_name: borrowerName,
        requested_amount: amount,
        currency: "USD",
        jurisdiction: "US",
      }),
    }),
  uploadDocument: (caseId: string, file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<Record<string, unknown>>(`/api/v1/cases/${caseId}/documents`, {
      method: "POST",
      body,
    });
  },
  startAnalysis: (caseId: string) =>
    request<Job>(`/api/v1/cases/${caseId}/analyze`, {
      method: "POST",
      headers: {"Idempotency-Key": crypto.randomUUID()},
    }),
  getJob: (jobId: string) => request<Job>(`/api/v1/jobs/${jobId}`),
  getAnalysis: (caseId: string) =>
    request<UnderwritingAnalysis>(`/api/v1/cases/${caseId}/analysis`),
  getReport: (caseId: string) => request<string>(`/api/v1/cases/${caseId}/report`),
  submitReview: (caseId: string, action: string, version: number, rationale: string) =>
    request<Record<string, unknown>>(`/api/v1/cases/${caseId}/review`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({action, rationale, expected_case_version: version}),
    }),
  async getAudit(caseId: string): Promise<AuditEvent[]> {
    return (await request<{items: AuditEvent[]}>(`/api/v1/cases/${caseId}/audit`)).items;
  },
  getMetrics: () => request<string>("/metrics"),
  getLatestEvaluation: () => request<Record<string, unknown>>("/api/v1/evaluations/latest"),
};

export function localRoleHeaders(): Record<string, string> {
  return {"X-Local-Roles": localStorage.getItem("creditrisk.roles") ?? "analyst,policy_admin"};
}
