from app.parsing.normalizer import StructuralNormalizer

RENAMED_A = """
int add(int a, int b) {
    int result = a + b; // sum
    return result;
}
"""

RENAMED_B = """
int compute(int x, int y) {
    int total = x + y;
    return total;
}
"""

DIFFERENT = """
void noop(void) {
    while (1) {
        break;
    }
}
"""


def test_extracts_functions() -> None:
    funcs = StructuralNormalizer().normalize_source(RENAMED_A)
    assert len(funcs) == 1
    assert funcs[0].name == "add"


def test_renaming_yields_identical_structure() -> None:
    norm = StructuralNormalizer()
    a = norm.normalize_source(RENAMED_A)[0]
    b = norm.normalize_source(RENAMED_B)[0]
    # Identifiers and comments normalized away => identical token streams.
    assert a.ast.token_stream() == b.ast.token_stream()


def test_structurally_different_code_differs() -> None:
    norm = StructuralNormalizer()
    a = norm.normalize_source(RENAMED_A)[0]
    d = norm.normalize_source(DIFFERENT)[0]
    assert a.ast.token_stream() != d.ast.token_stream()


def test_identifiers_are_anonymized() -> None:
    func = StructuralNormalizer().normalize_source(RENAMED_A)[0]
    signatures = func.ast.token_stream()
    # No identifier node should carry the original name.
    assert "add" not in signatures
    assert "result" not in signatures
    assert "identifier" in signatures


def test_callees_captured() -> None:
    source = """
    int helper(int x) { return x; }
    int main(void) { return helper(3); }
    """
    funcs = StructuralNormalizer().normalize_source(source)
    main = next(f for f in funcs if f.name == "main")
    assert "helper" in main.callees
