"""Parsing service: source code -> persistable structural artifacts.

Bridges the parsing layer and the winnowing algorithm. Each submission is
analyzed exactly once here; the resulting artifacts (normalized AST,
fingerprints, call edges) are stored and reused by every comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.algorithms.winnowing import Winnowing
from app.core.config import get_settings
from app.parsing.ast_nodes import ASTNode
from app.parsing.normalizer import StructuralNormalizer
from app.services.pipeline import FunctionArtifacts


@dataclass(slots=True)
class AnalyzedFunction:
    """A normalized function plus its winnowing fingerprints, ready to persist."""

    name: str
    order_index: int
    ast: ASTNode
    fingerprints: list[int]
    callees: list[str]
    ast_node_count: int

    def to_artifacts(self, ref: int | None = None) -> FunctionArtifacts:
        return FunctionArtifacts(
            name=self.name,
            ast=self.ast,
            fingerprints=set(self.fingerprints),
            callees=list(self.callees),
            ref=ref,
        )


class ParsingService:
    """Turns C source into :class:`AnalyzedFunction` records."""

    def __init__(
        self,
        normalizer: StructuralNormalizer | None = None,
        winnowing: Winnowing | None = None,
    ) -> None:
        settings = get_settings()
        self._normalizer = normalizer or StructuralNormalizer()
        self._winnowing = winnowing or Winnowing(
            k=settings.winnow_k, window=settings.winnow_window
        )

    def analyze(self, source: str) -> list[AnalyzedFunction]:
        """Parse, normalize and fingerprint every function in ``source``."""
        normalized = self._normalizer.normalize_source(source)
        analyzed: list[AnalyzedFunction] = []
        for fn in normalized:
            fingerprints = sorted(self._winnowing.fingerprints(fn.ast.token_stream()))
            analyzed.append(
                AnalyzedFunction(
                    name=fn.name,
                    order_index=fn.order_index,
                    ast=fn.ast,
                    fingerprints=fingerprints,
                    callees=fn.callees,
                    ast_node_count=fn.ast_node_count(),
                )
            )
        return analyzed
