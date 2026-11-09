# Production readiness checklist

- [ ] Institution policy owners approve configured rules and effective dates.
- [ ] Legal/privacy/fair-lending/model-risk reviews complete.
- [ ] OIDC, RBAC, RLS and privileged-access reviews pass.
- [ ] Malware scanning, data classification, retention and deletion are operational.
- [ ] Provider contracts, regional processing and no-training settings are approved.
- [ ] PostgreSQL migrations, PITR restores, RLS and pgvector load tests pass.
- [ ] SQS duplicate/restart/DLQ and provider/DB failure tests pass.
- [ ] S3 Object Lock retention and legal hold procedures are tested.
- [ ] SLOs, paging, dashboards, runbooks and on-call ownership are approved.
- [ ] Independent penetration test and dependency/container/IaC scans pass.
- [ ] Evaluation gates pass on representative governed datasets.
- [ ] Deployment rollback and disaster-recovery exercises pass.

This checklist supports readiness decisions; it is not a SOX or regulatory certification.
