"""Winnowing fingerprinting (Schleimer, Wilkinson & Aiken, 2003).

Contract:
    Winnowing.fingerprints(tokens) -> set[int]
        input:  a token sequence (here, the structural token stream of a
                normalized AST — already identifier/comment/format invariant).
        output: a set of selected 64-bit k-gram hashes (the document
                fingerprint).

    WinnowingSimilarity.similarity(tokens_a, tokens_b) -> SimilarityResult
        composes Winnowing with :class:`JaccardSimilarity`.

The hash is a deterministic, process-independent rolling hash (Python's builtin
``hash`` is salted per process and therefore unusable for persisted
fingerprints).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.algorithms.base import SimilarityResult
from app.algorithms.jaccard import JaccardSimilarity

_MOD = (1 << 61) - 1  # large Mersenne prime keeps hashes within 61 bits
_BASE = 1_000_003


def _stable_hash(token: str) -> int:
    """Deterministic polynomial hash of a single token string."""
    h = 0
    for ch in token:
        h = (h * _BASE + ord(ch)) % _MOD
    return h


def _kgram_hashes(tokens: Sequence[str], k: int) -> list[int]:
    """Rolling polynomial hashes of every contiguous k-gram of ``tokens``."""
    n = len(tokens)
    if n == 0:
        return []
    if n < k:
        # Treat the whole short stream as a single gram so tiny functions still
        # produce a fingerprint.
        return [_combine([_stable_hash(t) for t in tokens])]

    # Precompute per-token hashes, then combine windows of k.
    token_hashes = [_stable_hash(t) for t in tokens]
    grams: list[int] = []
    for i in range(n - k + 1):
        grams.append(_combine(token_hashes[i : i + k]))
    return grams


def _combine(values: Sequence[int]) -> int:
    """Combine a sequence of token hashes into one k-gram hash."""
    h = 0
    for v in values:
        h = (h * _BASE + v) % _MOD
    return h


class Winnowing:
    """Computes winnowing fingerprints from a token stream."""

    name = "winnowing"

    def __init__(self, k: int = 5, window: int = 4) -> None:
        if k < 1:
            raise ValueError("k must be >= 1")
        if window < 1:
            raise ValueError("window must be >= 1")
        self.k = k
        self.window = window

    def fingerprints(self, tokens: Sequence[str]) -> set[int]:
        """Return the set of selected fingerprint hashes for ``tokens``."""
        hashes = _kgram_hashes(tokens, self.k)
        if not hashes:
            return set()
        if len(hashes) <= self.window:
            # One window covering everything: select its minimum.
            return {min(hashes)}

        selected: set[int] = set()
        # Slide a window of size ``window`` over the k-gram hashes. In each
        # window select the minimum; on ties keep the rightmost occurrence
        # (the canonical winnowing tie-break), recording it once.
        min_pos = -1
        for i in range(len(hashes) - self.window + 1):
            window = hashes[i : i + self.window]
            # rightmost minimum within this window
            local_min = min(window)
            local_pos = i + max(
                idx for idx, val in enumerate(window) if val == local_min
            )
            if local_pos != min_pos:
                selected.add(hashes[local_pos])
                min_pos = local_pos
        return selected


class WinnowingSimilarity:
    """Winnowing + Jaccard: structural fingerprint similarity of two streams."""

    name = "winnowing_jaccard"

    def __init__(self, k: int = 5, window: int = 4) -> None:
        self._winnow = Winnowing(k=k, window=window)
        self._jaccard = JaccardSimilarity()

    def similarity(self, a: Sequence[str], b: Sequence[str], /) -> SimilarityResult:
        fp_a = self._winnow.fingerprints(a)
        fp_b = self._winnow.fingerprints(b)
        return self._jaccard.similarity(fp_a, fp_b)
