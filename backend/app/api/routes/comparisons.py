"""Comparison endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ComparisonServiceDep
from app.schemas.comparison import ComparisonRead, ComparisonRequest, ComparisonSummary
from app.services.comparison_service import SubmissionNotFoundError

router = APIRouter()


@router.post(
    "",
    response_model=ComparisonRead,
    status_code=status.HTTP_201_CREATED,
    summary="Compare two submissions structurally",
)
def create_comparison(
    payload: ComparisonRequest, service: ComparisonServiceDep
) -> ComparisonRead:
    try:
        comparison = service.compare(
            payload.submission_a_id,
            payload.submission_b_id,
            force=payload.force,
        )
    except SubmissionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {exc.args[0]} not found",
        ) from exc
    return _to_read(comparison)


@router.get("/{comparison_id}", response_model=ComparisonRead, summary="Get a comparison")
def get_comparison(comparison_id: int, service: ComparisonServiceDep) -> ComparisonRead:
    comparison = service.get(comparison_id)
    if comparison is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison not found")
    return _to_read(comparison)


@router.get(
    "/by-submission/{submission_id}",
    response_model=list[ComparisonSummary],
    summary="List comparisons involving a submission",
)
def list_for_submission(
    submission_id: int, service: ComparisonServiceDep
) -> list[ComparisonSummary]:
    return [
        ComparisonSummary.model_validate(c)
        for c in service.list_for_submission(submission_id)
    ]


def _to_read(comparison: object) -> ComparisonRead:
    return ComparisonRead.model_validate(comparison)
