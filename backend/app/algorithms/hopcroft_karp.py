"""Hopcroft–Karp maximum bipartite matching.

Contract:
    HopcroftKarp.match(adjacency, left, right) -> Matching
        input:  ``adjacency`` maps each left vertex to the set of compatible
                right vertices; ``left`` / ``right`` are the vertex collections.
        output: a :class:`Matching` giving the maximum set of vertex-disjoint
                edges and its size.

In CodeGuard this aligns the functions of one submission with those of another:
left = functions of A, right = functions of B, an edge exists when their
per-function similarity clears a threshold. The maximum matching is the optimal
order-independent alignment, which is exactly why function order never affects
the final score.

Runs in O(E·√V).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass
from typing import Generic, TypeVar

V = TypeVar("V", bound=Hashable)
_INF = float("inf")


@dataclass(frozen=True, slots=True)
class Matching(Generic[V]):
    """Result of a maximum bipartite matching."""

    #: left-vertex -> matched right-vertex
    pairs: dict[V, V]
    size: int


class HopcroftKarp:
    """Maximum cardinality matching in a bipartite graph."""

    name = "hopcroft_karp"

    def match(
        self,
        adjacency: Mapping[V, Iterable[V]],
        left: Iterable[V],
        right: Iterable[V],
    ) -> Matching[V]:
        left_vertices = list(left)
        right_vertices = list(right)
        adj: dict[V, list[V]] = {
            u: list(adjacency.get(u, ())) for u in left_vertices
        }

        # match_l[u] / match_r[v] hold the current partner or None.
        match_l: dict[V, V | None] = {u: None for u in left_vertices}
        match_r: dict[V, V | None] = {v: None for v in right_vertices}
        dist: dict[V, float] = {}

        def bfs() -> bool:
            queue: deque[V] = deque()
            for u in left_vertices:
                if match_l[u] is None:
                    dist[u] = 0.0
                    queue.append(u)
                else:
                    dist[u] = _INF
            found_augmenting = False
            while queue:
                u = queue.popleft()
                for v in adj[u]:
                    w = match_r[v]
                    if w is None:
                        found_augmenting = True
                    elif dist[w] == _INF:
                        dist[w] = dist[u] + 1
                        queue.append(w)
            return found_augmenting

        def dfs(u: V) -> bool:
            for v in adj[u]:
                w = match_r[v]
                if w is None or (dist[w] == dist[u] + 1 and dfs(w)):
                    match_l[u] = v
                    match_r[v] = u
                    return True
            dist[u] = _INF
            return False

        matching_size = 0
        while bfs():
            for u in left_vertices:
                if match_l[u] is None and dfs(u):
                    matching_size += 1

        pairs = {u: v for u, v in match_l.items() if v is not None}
        return Matching(pairs=pairs, size=matching_size)
