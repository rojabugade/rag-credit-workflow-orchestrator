from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "creditflow_http_requests_total", "HTTP requests", ["method", "route", "status"]
)
HTTP_LATENCY = Histogram(
    "creditflow_http_request_duration_seconds", "HTTP request duration", ["method", "route"]
)
WORKFLOW_JOBS = Gauge("creditflow_workflow_jobs", "Workflow jobs by status", ["status"])
WORKFLOW_FAILURES = Counter(
    "creditflow_workflow_failures_total", "Workflow failures", ["node", "error_type"]
)
RETRIEVAL_LATENCY = Histogram(
    "creditflow_retrieval_duration_seconds", "Retrieval duration", ["strategy"]
)
LLM_LATENCY = Histogram(
    "creditflow_llm_duration_seconds", "LLM request duration", ["provider", "model"]
)
LLM_TOKENS = Counter(
    "creditflow_llm_tokens_total", "LLM tokens", ["provider", "model", "direction"]
)
CACHE_OPERATIONS = Counter("creditflow_cache_operations_total", "Cache hit/miss", ["result"])
AWAITING_REVIEW = Gauge("creditflow_cases_awaiting_review", "Cases awaiting human review")
