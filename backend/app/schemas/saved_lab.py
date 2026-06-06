"""Schemas for saving and reopening password-protected score sets."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import AnalysisReport


class SavedLabCreate(BaseModel):
    """Request to persist an analysis report behind a unique name + password."""

    model_config = ConfigDict(str_strip_whitespace=True)

    label: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)
    report: AnalysisReport


class SavedLabSummary(BaseModel):
    """Confirmation returned to the saver (no scores revealed)."""

    id: int
    label: str
    created_at: datetime
    submission_count: int
    highest_student_score: float


class SavedLabUnlockRequest(BaseModel):
    """Name + password attempt to reopen a saved score set."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)
