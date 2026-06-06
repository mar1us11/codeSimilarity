"""Comparison service: orchestrate the pipeline over persisted submissions."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models.comparison import Comparison, FunctionMatch
from app.repositories.comparison_repository import ComparisonRepository
from app.repositories.submission_repository import SubmissionRepository
from app.services.artifacts import artifacts_from_function
from app.services.pipeline import SimilarityPipeline

logger = get_logger(__name__)


class SubmissionNotFoundError(LookupError):
    """Raised when a referenced submission does not exist."""


class ComparisonService:
    """Computes and persists structural comparisons between submissions."""

    def __init__(self, session: Session, pipeline: SimilarityPipeline | None = None) -> None:
        self._session = session
        self._submissions = SubmissionRepository(session)
        self._comparisons = ComparisonRepository(session)
        settings = get_settings()
        self._pipeline = pipeline or SimilarityPipeline(
            weights=settings.fusion_weights,
            match_threshold=settings.match_threshold,
        )

    def compare(
        self, submission_a_id: int, submission_b_id: int, *, force: bool = False
    ) -> Comparison:
        """Compare two submissions, caching the result for the (unordered) pair."""
        if not force:
            existing = self._comparisons.find_pair(submission_a_id, submission_b_id)
            if existing is not None:
                return existing

        sub_a = self._submissions.get_with_functions(submission_a_id)
        sub_b = self._submissions.get_with_functions(submission_b_id)
        if sub_a is None:
            raise SubmissionNotFoundError(submission_a_id)
        if sub_b is None:
            raise SubmissionNotFoundError(submission_b_id)

        artifacts_a = [artifacts_from_function(fn) for fn in sub_a.functions]
        artifacts_b = [artifacts_from_function(fn) for fn in sub_b.functions]

        result = self._pipeline.compare(artifacts_a, artifacts_b)
        logger.info(
            "Compared submissions %s vs %s -> overall=%.3f",
            submission_a_id,
            submission_b_id,
            result.overall_score,
        )

        # Replace any cached comparison when forcing.
        if force:
            stale = self._comparisons.find_pair(submission_a_id, submission_b_id)
            if stale is not None:
                self._comparisons.delete(stale)

        comparison = Comparison(
            submission_a_id=submission_a_id,
            submission_b_id=submission_b_id,
            overall_score=result.overall_score,
            ted_score=result.ted_score,
            winnow_score=result.winnow_score,
            callgraph_score=result.callgraph_score,
            status="completed",
            matches=[
                FunctionMatch(
                    function_a_id=m.ref_a,
                    function_b_id=m.ref_b,
                    similarity=m.similarity,
                    ted_similarity=m.ted_similarity,
                    winnow_similarity=m.winnow_similarity,
                )
                for m in result.matches
                if m.ref_a is not None and m.ref_b is not None
            ],
        )
        return self._comparisons.add(comparison)

    def get(self, comparison_id: int) -> Comparison | None:
        return self._comparisons.get_with_matches(comparison_id)

    def list_for_submission(self, submission_id: int) -> list[Comparison]:
        return self._comparisons.list_for_submission(submission_id)
