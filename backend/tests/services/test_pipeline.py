"""End-to-end pipeline tests on real C source (no database involved)."""

from app.services.parsing_service import ParsingService
from app.services.pipeline import SimilarityPipeline

PROGRAM = """
int add(int a, int b) {
    int result = a + b;
    return result;
}

int run(void) {
    return add(2, 3);
}
"""

# Same logic, renamed identifiers, comments added, functions reordered.
RENAMED_REORDERED = """
// reordered + renamed clone
int execute(void) {
    return sum(2, 3);
}

int sum(int x, int y) {
    int total = x + y; /* add them */
    return total;
}
"""

UNRELATED = """
void spin(void) {
    for (int i = 0; i < 10; i = i + 1) {
        while (i) {
            i = i - 1;
        }
    }
}
"""


def _artifacts(source: str):
    analyzed = ParsingService().analyze(source)
    return [a.to_artifacts(ref=i) for i, a in enumerate(analyzed)]


def test_identical_source_scores_one() -> None:
    pipeline = SimilarityPipeline()
    arts = _artifacts(PROGRAM)
    result = pipeline.compare(arts, arts)
    assert result.overall_score == 1.0


def test_renamed_and_reordered_clone_is_high() -> None:
    pipeline = SimilarityPipeline()
    result = pipeline.compare(_artifacts(PROGRAM), _artifacts(RENAMED_REORDERED))
    # Structural detector must see through renaming + reordering.
    assert result.overall_score > 0.85
    # Two functions each, both should align.
    assert len(result.matches) == 2


def test_unrelated_source_is_low() -> None:
    pipeline = SimilarityPipeline()
    result = pipeline.compare(_artifacts(PROGRAM), _artifacts(UNRELATED))
    assert result.overall_score < 0.5


def test_function_order_does_not_affect_score() -> None:
    pipeline = SimilarityPipeline()
    forward = _artifacts(PROGRAM)
    reversed_arts = list(reversed(_artifacts(PROGRAM)))
    a = pipeline.compare(forward, reversed_arts).overall_score
    b = pipeline.compare(forward, forward).overall_score
    assert a == b == 1.0
