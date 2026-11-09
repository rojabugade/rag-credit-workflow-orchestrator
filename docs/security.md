# Security and control design

- Production authentication validates OIDC signature, issuer, audience, expiry, subject, tenant, and roles. Local auth is configuration-gated and rejected in staging/production.
- Tenant IDs are derived from verified identity, never request bodies. PostgreSQL RLS adds defense in depth. Integration tests must execute with a non-owner application role because table owners bypass RLS.
- Uploads are size/type/magic validated, checksummed, privately stored, encrypted with KMS, malware-scanned in deployment, and exposed only through short-lived signed URLs.
- Retrieved/uploaded text is untrusted. Prompts delimit it as evidence; document instructions cannot alter system policy or tool authorization. Tools are allowlisted and schema validated; no arbitrary SQL or code execution exists.
- Logs/traces exclude source text, borrower identifiers, account numbers, tokens, and secrets. Metrics use bounded labels only.
- Audit events are append-only and hash chained. Production can replicate signed evidence manifests to an S3 Object Lock compliance-mode bucket with independently governed retention. This supports controls; it does not itself certify SOX compliance.
- Secrets come from Secrets Manager/task identity. IAM, security groups, private subnets, TLS, dependency scanning, image scanning, and egress allowlists are required.

Before real use: complete threat modeling, penetration testing, fair-lending impact analysis, privacy assessment, legal review, model-risk validation, explainability review, accessibility review, data retention approval, and formal change/access controls.
