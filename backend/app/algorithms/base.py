"""Shared algorithm contracts.

A *similarity algorithm* maps a pair of inputs of some type ``T`` to a
:class:`SimilarityResult` whose ``score`` is normalized to ``[0, 1]`` (1 means
structurally identical). The ``detail`` mapping carries algorithm-specific
diagnostics used for explainability in the API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, TypeVar, runtime_checkable

T_contra = TypeVar("T_contra", contravariant=True)


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """Normalized output of a similarity algorithm."""

    score: float
    detail: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"similarity score out of range: {self.score}")


@runtime_checkable
class SimilarityAlgorithm(Protocol[T_contra]):
    """Structural similarity between two inputs of the same type."""

    name: str

    def similarity(self, a: T_contra, b: T_contra, /) -> SimilarityResult:
        """Return the normalized similarity between ``a`` and ``b``."""
        ...
