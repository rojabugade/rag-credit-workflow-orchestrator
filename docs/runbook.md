# Operations runbook

## Queue backlog
Check receive count, age, worker desired/running tasks, CPU/memory, provider throttling, and DB pool saturation. Increase concurrency only within DB/provider quotas. Redrive DLQ only after fixing the cause and confirming job idempotency.

## Workflow failure
Locate by request/job/thread ID (never borrower data). Inspect the last checkpoint and typed failure. Retry transient providers within policy; do not bypass verification. Escalate corrupt/missing evidence to an analyst.

## Provider outage
Circuit-break the route, use an approved capability-compatible fallback through LiteLLM, or pause jobs. Never downgrade structured-output/tool requirements silently. Reconcile usage/cost events after recovery.

## Suspected tenant exposure
Disable affected access, preserve immutable logs, invoke incident response and legal/privacy notification procedures, rotate credentials, verify RLS/session tenant settings, and do not delete evidence.

## Database recovery
Stop writes, restore PITR into an isolated instance, validate hash chains/checkpoints and tenant policies, then perform approved cutover. Run quarterly restore exercises.

## Troubleshooting local mode
`uv run pytest` validates the credential-free workflow. A failed upload usually means MIME/magic/size validation. Docker/Terraform errors require those binaries; this environment did not have them. `GET /health/ready` exposes mock/live mode without secrets.
