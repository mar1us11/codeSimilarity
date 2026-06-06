from app.algorithms.call_graph import CallGraph, CallGraphSimilarity
from app.parsing.ast_nodes import ASTNode, NormalizedFunction


def fn(name: str, callees: list[str]) -> NormalizedFunction:
    return NormalizedFunction(name=name, order_index=0, ast=ASTNode("function_definition"), callees=callees)


def test_build_resolves_internal_edges_only() -> None:
    functions = [
        fn("main", ["helper", "printf"]),  # printf is external -> dropped
        fn("helper", []),
    ]
    graph = CallGraph.from_functions(functions)
    assert set(graph.nodes) == {"main", "helper"}
    assert graph.edges == (("main", "helper"),)


def test_identical_graphs_are_similar() -> None:
    a = CallGraph.from_functions([fn("main", ["a", "b"]), fn("a", []), fn("b", [])])
    b = CallGraph.from_functions([fn("root", ["x", "y"]), fn("x", []), fn("y", [])])
    # Same shape, different names -> high structural similarity.
    assert CallGraphSimilarity().similarity(a, b).score == 1.0


def test_empty_graphs_identical() -> None:
    empty = CallGraph(nodes=(), edges=())
    assert CallGraphSimilarity().similarity(empty, empty).score == 1.0


def test_degree_signature_counts() -> None:
    graph = CallGraph.from_functions([fn("main", ["a", "b"]), fn("a", []), fn("b", [])])
    signature = graph.degree_signature()
    # main: in=0,out=2 ; a: in=1,out=0 ; b: in=1,out=0
    assert signature[(0, 2)] == 1
    assert signature[(1, 0)] == 2


def test_component_count() -> None:
    graph = CallGraph.from_functions([fn("a", ["b"]), fn("b", []), fn("c", [])])
    assert graph.component_count() == 2
