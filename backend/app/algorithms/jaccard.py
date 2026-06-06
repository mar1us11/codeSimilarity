"""Jaccard similarity over hashable sets.

Contract:
    input:  two ``set`` (or iterables) of hashable items (typically winnowing
            fingerprints, i.e. ``int`` hashes).
    output: ``SimilarityResult`` with ``score = |A ∩ B| / |A ∪ B|``.

Two empty sets are defined to be identical (score 1.0): an empty function body
matches another empty function body.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from app.algorithms.base import SimilarityResult

H = TypeVar("H")


def jaccard_coefficient(a: set[H], b: set[H]) -> float:
    """Raw Jaccard coefficient of two sets."""
    if not a and not b:
        return 1.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


class JaccardSimilarity:
    """Jaccard set-similarity algorithm."""

    name = "jaccard"

    def similarity(self, a: Iterable[H], b: Iterable[H], /) -> SimilarityResult:
        set_a = set(a)
        set_b = set(b)
        score = jaccard_coefficient(set_a, set_b)
        return SimilarityResult(
            score=score,
            detail={
                "intersection": float(len(set_a & set_b)),
                "union": float(len(set_a | set_b)),
                "size_a": float(len(set_a)),
                "size_b": float(len(set_b)),
            },
        )
