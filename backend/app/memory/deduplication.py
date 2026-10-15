import re
from typing import Sequence


def normalize_text(text: str) -> set[str]:
    """Extract normalized lowercase tokens from text."""
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    return set(words)


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def is_duplicate(
    candidate: str,
    existing_items: Sequence[str],
    similarity_threshold: float = 0.80,
) -> tuple[bool, str | None, float]:
    """Check if candidate text is a duplicate of any existing text.

    Returns:
        (is_dup, matching_existing_text, highest_similarity)
    """
    cand_tokens = normalize_text(candidate)
    if not cand_tokens:
        return False, None, 0.0

    best_match = None
    best_sim = 0.0

    for existing in existing_items:
        # 1. Exact string match
        if candidate.strip().lower() == existing.strip().lower():
            return True, existing, 1.0

        # 2. Token overlap similarity
        ex_tokens = normalize_text(existing)
        sim = jaccard_similarity(cand_tokens, ex_tokens)
        if sim > best_sim:
            best_sim = sim
            best_match = existing

        if sim >= similarity_threshold:
            return True, existing, sim

    return False, best_match, best_sim
