# LangGraph workflow

`src/creditflow/workflows/graph.py` builds a real typed `StateGraph`. Financial calculations precede risk rules; compliance is independent and joins risk at verification. Verification retries are bounded and unsupported citations are removed—not invented. Exhausted verification creates an insufficient-data recommendation.

`interrupt()` pauses at human review. Resume uses `Command(resume=...)` and the same `thread_id`. Production uses `PostgresSaver`; local/test uses `InMemorySaver`. Completed calculations occur before the interrupt and are checkpointed. The interrupt node contains no pre-interrupt side effect because LangGraph restarts that node when resumed.

See `src/creditflow/workflows/diagram.mmd` for the Mermaid graph.
