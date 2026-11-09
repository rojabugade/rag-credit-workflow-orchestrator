# Database

```mermaid
erDiagram
  TENANTS ||--o{ USERS : owns
  USERS ||--o{ USER_ROLES : has
  TENANTS ||--o{ CREDIT_CASES : owns
  BORROWERS ||--o{ CREDIT_CASES : applies
  CREDIT_CASES ||--o{ DOCUMENTS : contains
  DOCUMENTS ||--o{ DOCUMENT_VERSIONS : versions
  DOCUMENT_VERSIONS ||--o{ DOCUMENT_CHUNKS : chunks
  CREDIT_CASES ||--o{ FINANCIAL_FACTS : facts
  CREDIT_CASES ||--o{ FINANCIAL_METRICS : metrics
  CREDIT_CASES ||--o{ CREDIT_ANALYSES : analyses
  CREDIT_ANALYSES ||--o{ RISK_FINDINGS : flags
  CREDIT_ANALYSES ||--o{ COMPLIANCE_FINDINGS : findings
  POLICY_DOCUMENTS ||--o{ COMPLIANCE_FINDINGS : supports
  CREDIT_CASES ||--o{ WORKFLOW_RUNS : workflows
  WORKFLOW_RUNS ||--o{ WORKFLOW_CHECKPOINTS : records
  CREDIT_CASES ||--o{ BACKGROUND_JOBS : jobs
  CREDIT_CASES ||--o{ HUMAN_REVIEWS : reviews
  CREDIT_CASES ||--o{ AUDIT_EVENTS : audits
```

Money uses fixed-precision numeric fields and Python `Decimal`. Timestamps are UTC. Case updates use SQLAlchemy version columns. Every tenant-owned table includes/indexes `tenant_id`; RLS policies use transaction-local `app.tenant_id`. Audit mutation/revocation is denied to application roles in production grants.
