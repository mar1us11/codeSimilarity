"""Function call-graph construction and structural comparison.

Contract:
    CallGraph.from_functions(functions) -> CallGraph
        builds the directed intra-submission call graph (nodes = functions,
        edges = "caller calls callee", restricted to calls that resolve to
        another function in the same submission).

    CallGraphSimilarity.similarity(graph_a, graph_b) -> SimilarityResult
        compares two call graphs by *shape* only — degree signatures, edge
        density and weakly-connected-component structure — never by function
        names. This captures how a program is decomposed into cooperating
        routines, a structural fingerprint that survives renaming and
        reordering.

DFS/BFS connected components (see :mod:`app.algorithms.graph_traversal`) supply
the component term.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from app.algorithms.base import SimilarityResult
from app.algorithms.graph_traversal import ConnectedComponents
from app.parsing.ast_nodes import NormalizedFunction


@dataclass(frozen=True, slots=True)
class CallGraph:
    """Directed call graph of a single submission."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    @classmethod
    def from_functions(cls, functions: Sequence[NormalizedFunction]) -> CallGraph:
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
        return cls(nodes=tuple(sorted(names)), edges=tuple(edges))

    # structural features
    def degree_signature(self) -> Counter[tuple[int, int]]:
        """Multiset of ``(in_degree, out_degree)`` over all nodes."""
        in_deg: dict[str, int] = {n: 0 for n in self.nodes}
        out_deg: dict[str, int] = {n: 0 for n in self.nodes}
        for caller, callee in self.edges:
            out_deg[caller] += 1
            in_deg[callee] += 1
        return Counter((in_deg[n], out_deg[n]) for n in self.nodes)

    def component_count(self) -> int:
        """Number of weakly-connected components (ignoring self-loops)."""
        proper_edges = [(u, v) for u, v in self.edges if u != v]
        return ConnectedComponents().count(self.nodes, proper_edges)


def _multiset_jaccard(a: Counter[tuple[int, int]], b: Counter[tuple[int, int]]) -> float:
    """Jaccard similarity of two multisets represented as Counters."""
    if not a and not b:
        return 1.0
    intersection = sum((a & b).values())
    union = sum((a | b).values())
    return intersection / union if union else 0.0


def _ratio(x: int, y: int) -> float:
    """Symmetric size-ratio similarity in [0, 1]."""
    if x == 0 and y == 0:
        return 1.0
    return min(x, y) / max(x, y)


class CallGraphSimilarity:
    """Compares the shape of two call graphs."""

    name = "call_graph"

    #: Sub-weights for the three structural terms (sum to 1).
    _W_DEGREE = 0.6
    _W_EDGES = 0.2
    _W_COMPONENTS = 0.2

    def similarity(self, a: CallGraph, b: CallGraph, /) -> SimilarityResult:
        if not a.nodes and not b.nodes:
            return SimilarityResult(score=1.0, detail={"nodes_a": 0.0, "nodes_b": 0.0})

        degree_sim = _multiset_jaccard(a.degree_signature(), b.degree_signature())
        edge_sim = _ratio(len(a.edges), len(b.edges))

        comp_a, comp_b = a.component_count(), b.component_count()
        component_sim = _ratio(comp_a, comp_b)

        score = (
            self._W_DEGREE * degree_sim
            + self._W_EDGES * edge_sim
            + self._W_COMPONENTS * component_sim
        )
        return SimilarityResult(
            score=max(0.0, min(1.0, score)),
            detail={
                "degree_similarity": degree_sim,
                "edge_similarity": edge_sim,
                "component_similarity": component_sim,
                "nodes_a": float(len(a.nodes)),
                "nodes_b": float(len(b.nodes)),
                "edges_a": float(len(a.edges)),
                "edges_b": float(len(b.edges)),
            },
        )


def build_edges(functions: Iterable[NormalizedFunction]) -> list[tuple[str, str]]:
    """Convenience helper returning resolved call edges for ``functions``."""
    return list(CallGraph.from_functions(list(functions)).edges)
