# API

OpenAPI is generated at `/docs` and `/openapi.json`. All writes require an `Idempotency-Key` where exposed. Analysis returns `202`; poll `/jobs/{id}`. A human review requires the current case version to prevent stale decisions. Tenant identity always comes from OIDC claims.

Errors use `{ "error": { "code", "message", "request_id", "details" } }`. Request IDs are accepted/returned as `X-Request-ID`. Report media type is Markdown text; analysis is strict JSON.

The machine recommendation schema is versioned (`schema_version=1.0`). Additive evolution uses a new minor version; removed/changed meanings require a new major endpoint/schema and a migration window.
