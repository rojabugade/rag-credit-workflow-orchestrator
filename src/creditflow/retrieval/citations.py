from creditflow.retrieval.models import SearchResult


def build_grounded_context(results: list[SearchResult], *, max_chars: int = 12000) -> str:
    blocks: list[str] = []
    used = 0
    for result in results:
        block = f"[SOURCE {result.citation_id}]\n{result.text}\n[/SOURCE]"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def validate_citations(claim_source_ids: list[str], retrieved: list[SearchResult]) -> list[str]:
    valid = {result.citation_id for result in retrieved}
    return sorted(set(claim_source_ids) - valid)
