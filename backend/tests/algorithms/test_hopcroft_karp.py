from app.algorithms.hopcroft_karp import HopcroftKarp


def test_perfect_matching() -> None:
    adjacency = {0: [0, 1], 1: [0], 2: [2]}
    result = HopcroftKarp().match(adjacency, [0, 1, 2], [0, 1, 2])
    assert result.size == 3
    # every left vertex is matched to a distinct right vertex
    assert len(set(result.pairs.values())) == 3


def test_matching_respects_capacity() -> None:
    # Two left vertices competing for a single right vertex.
    adjacency = {0: [0], 1: [0]}
    result = HopcroftKarp().match(adjacency, [0, 1], [0])
    assert result.size == 1


def test_empty_graph() -> None:
    result = HopcroftKarp().match({}, [], [])
    assert result.size == 0
    assert result.pairs == {}


def test_no_edges_yields_no_matches() -> None:
    result = HopcroftKarp().match({0: [], 1: []}, [0, 1], [0, 1])
    assert result.size == 0


def test_maximum_cardinality_classic() -> None:
    # Bipartite graph with a known maximum matching of size 3.
    adjacency = {
        "a": ["x"],
        "b": ["x", "y"],
        "c": ["y", "z"],
    }
    result = HopcroftKarp().match(adjacency, ["a", "b", "c"], ["x", "y", "z"])
    assert result.size == 3
