import math
import re
from collections.abc import Callable


def fixed_size_chunks(text: str, *, size: int = 1200, overlap: int = 120) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap smaller than size")
    normalized = text.strip()
    if not normalized:
        return []
    step = size - overlap
    return [normalized[start : start + size] for start in range(0, len(normalized), step)]


def recursive_chunks(
    text: str,
    *,
    max_chars: int = 1200,
    separators: tuple[str, ...] = ("\n\n", "\n", ". ", " "),
) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]
    separator = next((item for item in separators if item in normalized), "")
    if not separator:
        return fixed_size_chunks(normalized, size=max_chars, overlap=0)
    parts = normalized.split(separator)
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current}{separator if current else ''}{part}".strip()
        if current and len(candidate) > max_chars:
            chunks.extend(recursive_chunks(current, max_chars=max_chars, separators=separators[1:]))
            current = part
        else:
            current = candidate
    if current:
        chunks.extend(recursive_chunks(current, max_chars=max_chars, separators=separators[1:]))
    return chunks


def semantic_chunks(
    text: str,
    embed: Callable[[str], list[float]],
    *,
    similarity_threshold: float = 0.72,
    max_chars: int = 1600,
) -> list[str]:
    """Group adjacent sentences while their supplied embeddings remain semantically similar."""
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    if not sentences:
        return []
    chunks = [sentences[0]]
    previous_vector = embed(sentences[0])
    for sentence in sentences[1:]:
        vector = embed(sentence)
        similarity = _cosine(previous_vector, vector)
        candidate = f"{chunks[-1]} {sentence}"
        if similarity >= similarity_threshold and len(candidate) <= max_chars:
            chunks[-1] = candidate
        else:
            chunks.append(sentence)
        previous_vector = vector
    return chunks


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        raise ValueError("embedding vectors must be non-empty and have equal dimensions")
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    return (
        sum(a * b for a, b in zip(left, right, strict=True)) / denominator if denominator else 0.0
    )
