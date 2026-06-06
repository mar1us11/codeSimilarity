"""Shared FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.services.analysis_service import AnalysisService
from app.services.comparison_service import ComparisonService
from app.services.saved_lab_service import SavedLabService
from app.services.submission_service import SubmissionService

SessionDep = Annotated[Session, Depends(get_session)]


def get_workspace(
    x_workspace: Annotated[str | None, Header()] = None,
) -> str:
    """Resolve the caller's per-browser workspace token from the request header.

    Submissions are scoped to this token, so it is required for any endpoint
    that reads or writes them. The frontend sends it on every request.
    """
    if x_workspace is None or not x_workspace.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Workspace header.",
        )
    return x_workspace.strip()


WorkspaceDep = Annotated[str, Depends(get_workspace)]


def get_submission_service(session: SessionDep) -> Iterator[SubmissionService]:
    yield SubmissionService(session)


def get_comparison_service(session: SessionDep) -> Iterator[ComparisonService]:
    yield ComparisonService(session)


def get_analysis_service(session: SessionDep) -> Iterator[AnalysisService]:
    yield AnalysisService(session)


def get_saved_lab_service(session: SessionDep) -> Iterator[SavedLabService]:
    yield SavedLabService(session)


SubmissionServiceDep = Annotated[SubmissionService, Depends(get_submission_service)]
ComparisonServiceDep = Annotated[ComparisonService, Depends(get_comparison_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
SavedLabServiceDep = Annotated[SavedLabService, Depends(get_saved_lab_service)]
