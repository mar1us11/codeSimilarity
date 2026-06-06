from app.algorithms.graph_traversal import ConnectedComponents


def _normalize(components: list[set]) -> set[frozenset]:
    return {frozenset(component) for component in components}


def test_two_components() -> None:
    cc = ConnectedComponents()
    nodes = [1, 2, 3, 4, 5]
    edges = [(1, 2), (2, 3), (4, 5)]
    expected = {frozenset({1, 2, 3}), frozenset({4, 5})}
    assert _normalize(cc.dfs(nodes, edges)) == expected
    assert _normalize(cc.bfs(nodes, edges)) == expected


def test_dfs_and_bfs_agree() -> None:
    cc = ConnectedComponents()
    nodes = list(range(8))
    edges = [(0, 1), (1, 2), (3, 4), (5, 6), (6, 7), (7, 5)]
    assert _normalize(cc.dfs(nodes, edges)) == _normalize(cc.bfs(nodes, edges))


def test_isolated_nodes_each_own_component() -> None:
    cc = ConnectedComponents()
    assert cc.count([1, 2, 3], []) == 3


def test_count_single_component() -> None:
    cc = ConnectedComponents()
    assert cc.count([1, 2, 3], [(1, 2), (2, 3)]) == 1
