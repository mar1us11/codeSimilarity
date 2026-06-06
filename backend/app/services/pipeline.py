"""The structural-similarity pipeline.

This is the analysis engine's core: a pure, database-free function that takes
the normalized artifacts of two submissions and fuses every algorithm into a
single explainable score.

Data flow::

    functions A ─┐
                 ├─ per-function similarity matrix  (Tree Edit Distance
    functions B ─┘                                   + winnowing/Jaccard)
                 │
                 ├─ threshold edges ─► Hopcroft–Karp maximum matching
                 │                     (aligns functions; order-independent)
                 │
                 ├─ aligned TED / winnowing aggregates
                 │
                 └─ Call-graph similarity (degree + DFS/BFS components)
                         │
                         ▼
                 weighted fusion ─► overall score ∈ [0, 1]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.algorithms.call_graph import CallGraph, CallGraphSimilarity
from app.algorithms.hopcroft_karp import HopcroftKarp
from app.algorithms.jaccard import jaccard_coefficient
from app.algorithms.tree_edit_distance import TreeEditDistance
from app.parsing.ast_nodes import ASTNode


@dataclass(slots=True)
class FunctionArtifacts:
    """Precomputed structural artifacts of a single function.

    These are produced once by :class:`~app.services.parsing_service.ParsingService`
    (and persisted), then reused for every pairwise comparison.
    """

    name: str
    ast: ASTNode
    fingerprints: set[int]
    callees: list[str]
    #: Optional stable identifier (e.g. DB id) used to label matches.
    ref: int | None = None


@dataclass(frozen=True, slots=True)
class FunctionMatchResult:
    """One aligned function pair from the bipartite matching."""

    index_a: int
    index_b: int
    ref_a: int | None
    ref_b: int | None
    similarity: float
    ted_similarity: float
    winnow_similarity: float


@dataclass(slots=True)
class PipelineResult:
    """Fused result of comparing two submissions."""

    overall_score: float
    ted_score: float
    winnow_score: float
    callgraph_score: float
    matches: list[FunctionMatchResult] = field(default_factory=list)


class SimilarityPipeline:
    """Fuses all structural algorithms into an order-independent score."""

    def __init__(
        self,
        weights: tuple[float, float, float] = (0.5, 0.35, 0.15),
        match_threshold: float = 0.6,
    ) -> None:
        self._w_ted, self._w_winnow, self._w_callgraph = weights
        self._match_threshold = match_threshold
        self._ted = TreeEditDistance()
        self._matcher = HopcroftKarp()
        self._callgraph_sim = CallGraphSimilarity()

    # relative split of TED vs winnowing used for per-function edge weight
    @property
    def _ted_share(self) -> float:
        denom = self._w_ted + self._w_winnow
        return self._w_ted / denom if denom else 0.5

    def compare(
        self,
        functions_a: list[FunctionArtifacts],
        functions_b: list[FunctionArtifacts],
    ) -> PipelineResult:
        ted_matrix, winnow_matrix, combined = self._similarity_matrices(
            functions_a, functions_b
        )
        matches = self._match(functions_a, functions_b, ted_matrix, winnow_matrix, combined)

        denom = max(len(functions_a), len(functions_b))
        if denom == 0:
            aligned_ted = aligned_winnow = 1.0
        else:
            aligned_ted = sum(m.ted_similarity for m in matches) / denom
            aligned_winnow = sum(m.winnow_similarity for m in matches) / denom

        callgraph_score = self._callgraph_sim.similarity(
            self._call_graph(functions_a), self._call_graph(functions_b)
        ).score

        overall = (
            self._w_ted * aligned_ted
            + self._w_winnow * aligned_winnow
            + self._w_callgraph * callgraph_score
        )
        return PipelineResult(
            overall_score=round(max(0.0, min(1.0, overall)), 6),
            ted_score=round(aligned_ted, 6),
            winnow_score=round(aligned_winnow, 6),
            callgraph_score=round(callgraph_score, 6),
            matches=matches,
        )

    # -- internals -----------------------------------------------------------
    def _similarity_matrices(
        self,
        a: list[FunctionArtifacts],
        b: list[FunctionArtifacts],
    ) -> tuple[list[list[float]], list[list[float]], list[list[float]]]:
        ted = [[0.0] * len(b) for _ in a]
        winnow = [[0.0] * len(b) for _ in a]
        combined = [[0.0] * len(b) for _ in a]
        ted_share = self._ted_share
        for i, fa in enumerate(a):
            for j, fb in enumerate(b):
                ted_sim = self._ted.similarity(fa.ast, fb.ast).score
                winnow_sim = jaccard_coefficient(fa.fingerprints, fb.fingerprints)
                ted[i][j] = ted_sim
                winnow[i][j] = winnow_sim
                combined[i][j] = ted_share * ted_sim + (1 - ted_share) * winnow_sim
        return ted, winnow, combined

    def _match(
        self,
        a: list[FunctionArtifacts],
        b: list[FunctionArtifacts],
        ted_matrix: list[list[float]],
        winnow_matrix: list[list[float]],
        combined: list[list[float]],
    ) -> list[FunctionMatchResult]:
        # Build threshold edges; Hopcroft–Karp then maximizes aligned pairs.
        adjacency: dict[int, list[int]] = {}
        for i in range(len(a)):
            partners = [
                j for j in range(len(b)) if combined[i][j] >= self._match_threshold
            ]
            # Prefer stronger candidates first so the augmenting search tends to
            # lock in high-similarity pairs.
            partners.sort(key=lambda j: combined[i][j], reverse=True)  # noqa: B023
            adjacency[i] = partners

        matching = self._matcher.match(adjacency, range(len(a)), range(len(b)))

        results: list[FunctionMatchResult] = []
        for i, j in matching.pairs.items():
            results.append(
                FunctionMatchResult(
                    index_a=i,
                    index_b=j,
                    ref_a=a[i].ref,
                    ref_b=b[j].ref,
                    similarity=round(combined[i][j], 6),
                    ted_similarity=round(ted_matrix[i][j], 6),
                    winnow_similarity=round(winnow_matrix[i][j], 6),
                )
            )
        results.sort(key=lambda m: m.similarity, reverse=True)
        return results

    def _call_graph(self, functions: list[FunctionArtifacts]) -> CallGraph:
        names = {fn.name for fn in functions}
        edges: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for fn in functions:
            for callee in fn.callees:
                if callee in names:
                    edge = (fn.name, callee)
                    if edge not in seen:
                        seen.add(edge)
                        edges.append(edge)
        return CallGraph(nodes=tuple(sorted(names)), edges=tuple(edges))
