# Performance and measurement

The resume-inspired scale/benefit numbers are targets, not achieved results. Multi-agent underwriting is asynchronous and is not expected to finish in 450 ms.

Measure separately:

- cached metadata API p50/p95/p99;
- vector, keyword, hybrid, and hybrid+rereanking latency/precision;
- each provider call latency/tokens/cost;
- queue wait and full workflow wall time;
- analyst active time and escalation/revision rates.

Use `tests/load/locustfile.py`, Prometheus, `EXPLAIN (ANALYZE, BUFFERS)`, and fixed versioned evaluation sets. A retrieval improvement requires paired queries, identical relevance judgments, bootstrap confidence intervals, and before/after MRR/nDCG/precision—not anecdotal examples. Analyst-effort, parsing-defect, and inference-cost reductions require matched cohorts, stable definitions, and sufficient observation windows. Synthetic benchmark output must be labeled synthetic.

For 15M+ chunks: partition/index around tenant and active policy filters, batch embeddings, tune HNSW and autovacuum with measured recall/latency, use read replicas where appropriate, and test index build/reindex procedures. Local setup intentionally uses tiny fixtures.
