"""Cohort-analysis endpoint.

Runs an all-pairs structural comparison across submissions and, optionally,
compares each submission against freshly generated AI reference solutions.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import AnalysisServiceDep, WorkspaceDep
from app.core.config import get_settings
from app.schemas.analysis import AnalysisReport, AnalysisRequest
from app.services.analysis_service import AnalysisError

router = APIRouter()


class AnalysisCapabilities(BaseModel):
    """What the analysis engine can do in the current deployment."""

    ai_reference_available: bool
    default_reference_count: int
    max_reference_count: int


@router.get(
    "/capabilities",
    response_model=AnalysisCapabilities,
    summary="Report whether AI reference generation is configured",
)
def capabilities() -> AnalysisCapabilities:
    settings = get_settings()
    return AnalysisCapabilities(
        ai_reference_available=settings.openai_configured,
        default_reference_count=settings.ai_reference_default_count,
        max_reference_count=settings.ai_reference_max_count,
    )


@router.post(
    "",
    response_model=AnalysisReport,
    summary="Run an all-pairs cohort analysis (optionally vs AI references)",
)
def run_analysis(
    payload: AnalysisRequest, service: AnalysisServiceDep, workspace: WorkspaceDep
) -> AnalysisReport:
    try:
        return service.analyze(payload, workspace=workspace)
    except AnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
