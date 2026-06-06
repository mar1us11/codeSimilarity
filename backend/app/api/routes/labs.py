"""Saved score-set endpoints: persist analysis reports behind a password."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SavedLabServiceDep
from app.schemas.analysis import AnalysisReport
from app.schemas.saved_lab import SavedLabCreate, SavedLabSummary, SavedLabUnlockRequest
from app.services.saved_lab_service import (
    DuplicateLabNameError,
    InvalidLabCredentialsError,
)

router = APIRouter()


@router.post(
    "",
    response_model=SavedLabSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Save an analysis report behind a unique name + password",
)
def create_lab(payload: SavedLabCreate, service: SavedLabServiceDep) -> SavedLabSummary:
    try:
        return service.save(payload.label, payload.password, payload.report)
    except DuplicateLabNameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.post(
    "/unlock",
    response_model=AnalysisReport,
    summary="Reopen a saved score set by its name + password",
)
def unlock_lab(
    payload: SavedLabUnlockRequest, service: SavedLabServiceDep
) -> AnalysisReport:
    try:
        return service.unlock_by_name(payload.name, payload.password)
    except InvalidLabCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect name or password.",
        ) from exc
