"""Cohort analysis: all-pairs structural comparison + optional AI references.

This orchestrates the existing, unchanged :class:`SimilarityPipeline` over a
whole cohort instead of a single pair:

* every submission is compared against every other submission
  (student-vs-student similarity);
* when enabled, freshly generated AI reference solutions are parsed in-memory
  and every submission is compared against every reference
  (student-vs-reference similarity), reported separately;
* high-similarity student pairs are linked into a graph and DFS connected
  components surface *suspicious clusters* of likely collaboration.

AI references are ephemeral: they are parsed into in-memory artifacts, used for
the run, and discarded. They are never persisted and never appear as
submissions, so the system never classifies code as "AI generated".
"""

from __future__ import annotations

from datetime import UTC, datetime
from itertools import combinations
from typing import cast

from sqlalchemy.orm import Session

from app.algorithms.graph_traversal import ConnectedComponents
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models.submission import Submission
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.analysis import (
    AiReferenceSolution,
    AnalysisReport,
    AnalysisRequest,
    ClusterMember,
    ReferenceSimilarityResult,
    StudentPairResult,
    SubmissionReferenceSummary,
    SuspiciousCluster,
)
from app.services.ai_reference import AiReferenceError, AiReferenceService
from app.services.artifacts import artifacts_from_function
from app.services.parsing_service import ParsingService
from app.services.pipeline import FunctionArtifacts, SimilarityPipeline

logger = get_logger(__name__)


class AnalysisError(RuntimeError):
    """Raised for client-correctable analysis failures (safe to surface)."""


class AnalysisService:
    """Runs an all-pairs cohort analysis with optional AI reference comparison."""

    def __init__(
        self,
        session: Session,
        *,
        pipeline: SimilarityPipeline | None = None,
        ai_reference_service: AiReferenceService | None = None,
        parsing_service: ParsingService | None = None,
    ) -> None:
        self._submissions = SubmissionRepository(session)
        self._settings = get_settings()
        self._pipeline = pipeline or SimilarityPipeline(
            weights=self._settings.fusion_weights,
            match_threshold=self._settings.match_threshold,
        )
        self._ai = ai_reference_service or AiReferenceService(self._settings)
        self._parser = parsing_service or ParsingService()

    def analyze(self, request: AnalysisRequest, *, workspace: str) -> AnalysisReport:
        submissions = self._load_submissions(request.submission_ids, workspace)
        warnings: list[str] = []

        if len(submissions) < 2:
            warnings.append(
                "At least two submissions are required to compute student similarity."
            )

        student_artifacts = {sub.id: self._artifacts_for(sub) for sub in submissions}
        names = {sub.id: sub.name for sub in submissions}

        student_pairs = self._compare_students(submissions, student_artifacts)
        highest = max((p.overall_score for p in student_pairs), default=0.0)
        clusters = self._build_clusters(student_pairs, names)

        reference_results: list[ReferenceSimilarityResult] = []
        reference_summaries: list[SubmissionReferenceSummary] = []
        ai_references: list[AiReferenceSolution] = []
        ai_reference_count = 0

        if request.use_ai_reference:
            (
                reference_results,
                ai_references,
                ai_reference_count,
                ref_warnings,
            ) = self._compare_references(
                request, submissions, student_artifacts, names
            )
            warnings.extend(ref_warnings)
            reference_summaries = self._summarize_references(submissions, reference_results)

        return AnalysisReport(
            generated_at=datetime.now(UTC),
            submission_count=len(submissions),
            ai_reference_enabled=request.use_ai_reference,
            ai_reference_count=ai_reference_count,
            problem_description=request.problem_description if request.use_ai_reference else None,
            student_pairs=student_pairs,
            highest_student_score=round(highest, 6),
            clusters=clusters,
            ai_references=ai_references,
            reference_results=reference_results,
            reference_summaries=reference_summaries,
            warnings=warnings,
        )

    # -- loading -------------------------------------------------------------
    def _load_submissions(
        self, ids: list[int] | None, workspace: str
    ) -> list[Submission]:
        if not ids:
            return self._submissions.list_with_counts(
                workspace=workspace, limit=500, offset=0
            )
        unique_ids = list(dict.fromkeys(ids))  # de-dupe, preserve order
        loaded: list[Submission] = []
        for sid in unique_ids:
            sub = self._submissions.get_with_functions(sid, workspace=workspace)
            if sub is None:
                raise AnalysisError(f"Submission {sid} not found.")
            loaded.append(sub)
        return loaded

    @staticmethod
    def _artifacts_for(submission: Submission) -> list[FunctionArtifacts]:
        return [artifacts_from_function(fn) for fn in submission.functions]

    # -- student-vs-student --------------------------------------------------
    def _compare_students(
        self,
        submissions: list[Submission],
        artifacts: dict[int, list[FunctionArtifacts]],
    ) -> list[StudentPairResult]:
        pairs: list[StudentPairResult] = []
        for a, b in combinations(submissions, 2):
            result = self._pipeline.compare(artifacts[a.id], artifacts[b.id])
            pairs.append(
                StudentPairResult(
                    submission_a_id=a.id,
                    submission_a_name=a.name,
                    submission_b_id=b.id,
                    submission_b_name=b.name,
                    overall_score=result.overall_score,
                    ted_score=result.ted_score,
                    winnow_score=result.winnow_score,
                    callgraph_score=result.callgraph_score,
                    aligned_function_count=len(result.matches),
                )
            )
        pairs.sort(key=lambda p: p.overall_score, reverse=True)
        return pairs

    # -- clustering (DFS/BFS connected components) ---------------------------
    def _build_clusters(
        self, pairs: list[StudentPairResult], names: dict[int, str]
    ) -> list[SuspiciousCluster]:
        threshold = self._settings.cluster_threshold
        edges = [
            (p.submission_a_id, p.submission_b_id)
            for p in pairs
            if p.overall_score >= threshold
        ]
        if not edges:
            return []

        # Per-edge scores, keyed by the unordered pair, for cluster averaging.
        edge_score = {
            frozenset((p.submission_a_id, p.submission_b_id)): p.overall_score
            for p in pairs
        }
        nodes = list(names)
        components = ConnectedComponents().dfs(nodes, edges)

        clusters: list[SuspiciousCluster] = []
        for raw_component in components:
            component = cast("set[int]", raw_component)
            if len(component) < 2:
                continue
            internal = [
                score
                for pair, score in edge_score.items()
                if pair <= component and score >= threshold
            ]
            avg = sum(internal) / len(internal) if internal else 0.0
            members = sorted(component)
            clusters.append(
                SuspiciousCluster(
                    members=[
                        ClusterMember(submission_id=sid, name=names[sid]) for sid in members
                    ],
                    size=len(members),
                    average_similarity=round(avg, 6),
                )
            )
        clusters.sort(key=lambda c: (c.size, c.average_similarity), reverse=True)
        return clusters

    # -- student-vs-AI-reference ---------------------------------------------
    def _compare_references(
        self,
        request: AnalysisRequest,
        submissions: list[Submission],
        student_artifacts: dict[int, list[FunctionArtifacts]],
        names: dict[int, str],
    ) -> tuple[
        list[ReferenceSimilarityResult],
        list[AiReferenceSolution],
        int,
        list[str],
    ]:
        warnings: list[str] = []
        try:
            generated = self._ai.generate(
                request.problem_description or "", request.reference_count
            )
        except AiReferenceError as exc:
            # Don't fail the whole run: surface student similarity with a warning.
            logger.warning("AI reference generation skipped: %s", exc)
            return [], [], 0, [f"AI reference generation failed: {exc}"]

        reference_artifacts: list[tuple[str, list[FunctionArtifacts]]] = []
        ai_references: list[AiReferenceSolution] = []
        for ref in generated:
            analyzed = self._parser.analyze(ref.source_code)
            if not analyzed:
                warnings.append(
                    f"{ref.label} produced no parseable C functions and was skipped."
                )
                continue
            arts = [a.to_artifacts(ref=i) for i, a in enumerate(analyzed)]
            reference_artifacts.append((ref.label, arts))
            ai_references.append(
                AiReferenceSolution(label=ref.label, source_code=ref.source_code)
            )

        results: list[ReferenceSimilarityResult] = []
        for sub in submissions:
            for label, ref_arts in reference_artifacts:
                result = self._pipeline.compare(student_artifacts[sub.id], ref_arts)
                results.append(
                    ReferenceSimilarityResult(
                        submission_id=sub.id,
                        submission_name=names[sub.id],
                        reference_label=label,
                        overall_score=result.overall_score,
                        ted_score=result.ted_score,
                        winnow_score=result.winnow_score,
                        callgraph_score=result.callgraph_score,
                    )
                )
        results.sort(key=lambda r: r.overall_score, reverse=True)
        return results, ai_references, len(reference_artifacts), warnings

    @staticmethod
    def _summarize_references(
        submissions: list[Submission], results: list[ReferenceSimilarityResult]
    ) -> list[SubmissionReferenceSummary]:
        best: dict[int, ReferenceSimilarityResult] = {}
        for r in results:
            current = best.get(r.submission_id)
            if current is None or r.overall_score > current.overall_score:
                best[r.submission_id] = r
        summaries = [
            SubmissionReferenceSummary(
                submission_id=sub.id,
                submission_name=sub.name,
                max_reference_score=round(best[sub.id].overall_score, 6)
                if sub.id in best
                else 0.0,
                best_reference_label=best[sub.id].reference_label if sub.id in best else None,
            )
            for sub in submissions
        ]
        summaries.sort(key=lambda s: s.max_reference_score, reverse=True)
        return summaries
