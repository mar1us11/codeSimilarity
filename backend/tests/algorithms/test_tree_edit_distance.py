from app.algorithms.tree_edit_distance import TreeEditDistance
from app.parsing.ast_nodes import ASTNode


def leaf(label: str) -> ASTNode:
    return ASTNode(label=label)


def test_identical_trees_zero_distance() -> None:
    tree = ASTNode("root", children=[leaf("a"), leaf("b")])
    ted = TreeEditDistance()
    assert ted.distance(tree, tree) == 0
    assert ted.similarity(tree, tree).score == 1.0


def test_single_relabel_distance_one() -> None:
    a = ASTNode("root", children=[leaf("a"), leaf("b")])
    b = ASTNode("root", children=[leaf("a"), leaf("c")])
    assert TreeEditDistance().distance(a, b) == 1


def test_single_insert_distance_one() -> None:
    a = ASTNode("root", children=[leaf("a")])
    b = ASTNode("root", children=[leaf("a"), leaf("b")])
    assert TreeEditDistance().distance(a, b) == 1


def test_distance_is_symmetric() -> None:
    a = ASTNode("root", children=[leaf("a"), ASTNode("x", children=[leaf("y")])])
    b = ASTNode("root", children=[leaf("a")])
    ted = TreeEditDistance()
    assert ted.distance(a, b) == ted.distance(b, a)


def test_known_zhang_shasha_distance() -> None:
    # Classic example: f(d(a,c(b)))  vs  f(c(d(a,b)))  -> distance 2.
    a = ASTNode("f", children=[ASTNode("d", children=[leaf("a"), ASTNode("c", children=[leaf("b")])])])
    b = ASTNode("f", children=[ASTNode("c", children=[ASTNode("d", children=[leaf("a"), leaf("b")])])])
    assert TreeEditDistance().distance(a, b) == 2


def test_similarity_within_unit_interval() -> None:
    a = ASTNode("r", children=[leaf("a"), leaf("b"), leaf("c")])
    b = ASTNode("r", children=[leaf("x"), leaf("y")])
    score = TreeEditDistance().similarity(a, b).score
    assert 0.0 <= score <= 1.0


def test_operator_value_changes_distance() -> None:
    # Same shape, different operator => one relabel.
    a = ASTNode("binary_expression", value="+", children=[leaf("identifier"), leaf("identifier")])
    b = ASTNode("binary_expression", value="-", children=[leaf("identifier"), leaf("identifier")])
    assert TreeEditDistance().distance(a, b) == 1
