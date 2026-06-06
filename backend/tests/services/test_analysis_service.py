"""Cohort analysis tests using in-memory ORM objects (no database)."""

from __future__ import annotations

import pytest

from app.db.models.function import FunctionUnit
from app.db.models.submission import Submission
from app.schemas.analysis import AnalysisRequest
from app.services.ai_reference import AiReferenceError, GeneratedReference
from app.services.analysis_service import AnalysisService
from app.services.parsing_service import ParsingService

PROGRAM = """
int add(int a, int b) {
    int result = a + b;
    return result;
}

int run(void) {
    return add(2, 3);
}
"""

# Renamed + reordered clone of PROGRAM.
CLONE = """
int execute(void) {
    return sum(2, 3);
}

int sum(int x, int y) {
    int total = x + y;
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

_parser = ParsingService()


def _submission(sub_id: int, name: str, source: str) -> Submission:
    """Build a transient Submission with analyzed FunctionUnits (no session)."""
    analyzed = _parser.analyze(source)
    submission = Submission(name=name, filename=f"{name}.c", language="c", source_code=source)
    submission.id = sub_id
    submission.functions = [
        FunctionUnit(
            id=sub_id * 100 + i,
            name=fn.name,
            order_index=fn.order_index,
            ast_node_count=fn.ast_node_count,
            normalized_ast=fn.ast.to_dict(),
            fingerprints=fn.fingerprints,
            callees=fn.callees,
        )
        for i, fn in enumerate(analyzed)
    ]
    return submission


def _service(monkeypatch: pytest.MonkeyPatch, submissions: list[Submission]) -> AnalysisService:
    service = AnalysisService(session=object())  # type: ignore[arg-type]
    monkeypatch.setattr(service, "_load_submissions", lambda _ids, _ws: submissions)
    return service


def test_all_pairs_and_cluster_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    subs = [
        _submission(1, "Alice", PROGRAM),
        _submission(2, "Bob", CLONE),
        _submission(3, "Carol", UNRELATED),
    ]
    service = _service(monkeypatch, subs)

    report = service.analyze(AnalysisRequest(use_ai_reference=False), workspace="ws-test")

    # 3 submissions -> 3 unique unordered pairs.
    assert len(report.student_pairs) == 3
    # The Alice/Bob clone pair must be the strongest.
    top = report.student_pairs[0]
    assert {top.submission_a_id, top.submission_b_id} == {1, 2}
    assert top.overall_score > 0.85
    # Alice + Bob form a suspicious cluster; Carol stays out.
    assert len(report.clusters) == 1
    cluster = report.clusters[0]
    assert {m.submission_id for m in cluster.members} == {1, 2}
    assert cluster.size == 2
    # No AI references requested.
    assert report.ai_reference_enabled is False
    assert report.reference_results == []


def test_ai_reference_comparison(monkeypatch: pytest.MonkeyPatch) -> None:
    subs = [_submission(1, "Alice", PROGRAM), _submission(2, "Bob", UNRELATED)]
    service = _service(monkeypatch, subs)

    # Stub the provider: one reference identical to Alice's program.
    monkeypatch.setattr(
        service._ai,
        "generate",
        lambda _desc, _count: [GeneratedReference(label="AI Reference 1", source_code=PROGRAM)],
    )

    report = service.analyze(
        AnalysisRequest(
            use_ai_reference=True,
            problem_description="Add two integers and run it.",
            reference_count=1,
        ),
        workspace="ws-test",
    )

    assert report.ai_reference_enabled is True
    assert report.ai_reference_count == 1
    # One reference compared against each of the two submissions.
    assert len(report.reference_results) == 2
    assert len(report.ai_references) == 1
    assert report.ai_references[0].label == "AI Reference 1"
    assert report.ai_references[0].source_code == PROGRAM
    # Alice (identical to the reference) must score highest against it.
    best = report.reference_summaries[0]
    assert best.submission_id == 1
    assert best.max_reference_score > 0.85
    assert best.best_reference_label == "AI Reference 1"


def test_ai_failure_degrades_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    subs = [_submission(1, "Alice", PROGRAM), _submission(2, "Bob", CLONE)]
    service = _service(monkeypatch, subs)

    def _boom(_desc: str, _count: int) -> list[GeneratedReference]:
        raise AiReferenceError("provider down")

    monkeypatch.setattr(service._ai, "generate", _boom)

    report = service.analyze(
        AnalysisRequest(
            use_ai_reference=True,
            problem_description="whatever",
            reference_count=2,
        ),
        workspace="ws-test",
    )

    # Student similarity still computed; the AI failure is surfaced as a warning.
    assert len(report.student_pairs) == 1
    assert report.reference_results == []
    assert any("AI reference generation failed" in w for w in report.warnings)


def test_description_required_when_ai_enabled() -> None:
    with pytest.raises(ValueError, match="problem_description is required"):
        AnalysisRequest(use_ai_reference=True, problem_description="  ")
