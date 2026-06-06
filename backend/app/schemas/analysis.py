"""Cohort-analysis request/response schemas.

A single "analysis run" compares **every** submission against every other
submission and, optionally, against a set of freshly generated AI reference
solutions. Student-vs-student and student-vs-reference similarities are reported
separately and a reference is never used to label code as "AI generated" — only
to report similarity to a known-correct solution.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalysisRequest(BaseModel):
    """Configuration for one cohort analysis run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    #: Submissions to analyze. Empty/omitted means "every stored submission".
    submission_ids: list[int] | None = Field(
        default=None,
        description="Submissions to include; omit or leave empty to use all stored submissions.",
    )
    use_ai_reference: bool = Field(
        default=False,
        description="Generate AI reference solutions and compare each submission against them.",
    )
    problem_description: str | None = Field(
        default=None,
        max_length=8000,
        description="Assignment/problem statement; required when AI references are enabled.",
    )
    reference_count: int = Field(
        default=5,
        ge=1,
        le=50,
        description="How many AI reference solutions to generate (clamped server-side).",
    )

    @model_validator(mode="after")
    def _require_description_when_enabled(self) -> AnalysisRequest:
        if self.use_ai_reference and not (self.problem_description or "").strip():
            raise ValueError(
                "problem_description is required when use_ai_reference is enabled"
            )
        return self


class StudentPairResult(BaseModel):
    """Structural similarity between two student submissions."""

    submission_a_id: int
    submission_a_name: str
    submission_b_id: int
    submission_b_name: str
    overall_score: float
    ted_score: float
    winnow_score: float
    callgraph_score: float
    aligned_function_count: int


class ReferenceSimilarityResult(BaseModel):
    """Similarity of one submission to one AI reference solution."""

    submission_id: int
    submission_name: str
    reference_label: str
    overall_score: float
    ted_score: float
    winnow_score: float
    callgraph_score: float


class AiReferenceSolution(BaseModel):
    """One generated AI reference solution returned with the analysis run."""

    label: str
    source_code: str


class SubmissionReferenceSummary(BaseModel):
    """Best AI-reference match for a single submission."""

    submission_id: int
    submission_name: str
    max_reference_score: float
    best_reference_label: str | None


class ClusterMember(BaseModel):
    submission_id: int
    name: str


class SuspiciousCluster(BaseModel):
    """A group of submissions transitively linked by high similarity (DFS/BFS)."""

    members: list[ClusterMember]
    size: int
    average_similarity: float


class AnalysisReport(BaseModel):
    """Full result of a cohort analysis run (not persisted)."""

    generated_at: datetime
    submission_count: int
    ai_reference_enabled: bool
    ai_reference_count: int
    problem_description: str | None
    student_pairs: list[StudentPairResult]
    highest_student_score: float
    clusters: list[SuspiciousCluster]
    ai_references: list[AiReferenceSolution]
    reference_results: list[ReferenceSimilarityResult]
    reference_summaries: list[SubmissionReferenceSummary]
    warnings: list[str]
