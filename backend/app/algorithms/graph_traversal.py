"""Connected components via DFS and BFS.

Contract:
    ConnectedComponents.dfs(nodes, edges) -> list[set[Hashable]]
    ConnectedComponents.bfs(nodes, edges) -> list[set[Hashable]]
        input:  a vertex set and an undirected edge list.
        output: the connected components (as a list of vertex sets), each
                computed by the named traversal strategy.

Edges are treated as undirected so the routine yields *weakly* connected
components when applied to a directed call graph. Both strategies must produce
identical partitions; DFS and BFS are provided because the project explicitly
exercises both traversals.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterable

Vertex = Hashable


def _adjacency(
    nodes: Iterable[Vertex], edges: Iterable[tuple[Vertex, Vertex]]
) -> dict[Vertex, set[Vertex]]:
    adj: dict[Vertex, set[Vertex]] = {n: set() for n in nodes}
    for u, v in edges:
        adj.setdefault(u, set())
        adj.setdefault(v, set())
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return adj


class ConnectedComponents:
    """Undirected connected-component finder with DFS and BFS strategies."""

    name = "connected_components"

    def dfs(
        self,
        nodes: Iterable[Vertex],
        edges: Iterable[tuple[Vertex, Vertex]],
    ) -> list[set[Vertex]]:
        """Connected components found with iterative depth-first search."""
        adj = _adjacency(nodes, edges)
        visited: set[Vertex] = set()
        components: list[set[Vertex]] = []
        for start in adj:
            if start in visited:
                continue
            component: set[Vertex] = set()
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                stack.extend(adj[node] - visited)
            components.append(component)
        return components

    def bfs(
        self,
        nodes: Iterable[Vertex],
        edges: Iterable[tuple[Vertex, Vertex]],
    ) -> list[set[Vertex]]:
        """Connected components found with breadth-first search."""
        adj = _adjacency(nodes, edges)
        visited: set[Vertex] = set()
        components: list[set[Vertex]] = []
        for start in adj:
            if start in visited:
                continue
            component: set[Vertex] = set()
            queue: deque[Vertex] = deque([start])
            visited.add(start)
            while queue:
                node = queue.popleft()
                component.add(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
        return components

    def count(
        self,
        nodes: Iterable[Vertex],
        edges: Iterable[tuple[Vertex, Vertex]],
    ) -> int:
        """Number of connected components (uses BFS)."""
        return len(self.bfs(nodes, edges))
