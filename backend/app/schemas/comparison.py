"""Comparison request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ComparisonRequest(BaseModel):
    """Request to compare two submissions."""

    submission_a_id: int = Field(gt=0)
    submission_b_id: int = Field(gt=0)
    force: bool = Field(
        default=False,
        description="Recompute even if a cached comparison for the pair exists.",
    )

    @model_validator(mode="after")
    def _distinct(self) -> ComparisonRequest:
        if self.submission_a_id == self.submission_b_id:
            raise ValueError("cannot compare a submission with itself")
        return self


class FunctionMatchRead(BaseModel):
    """An aligned function pair within a comparison."""

    model_config = ConfigDict(from_attributes=True)

    function_a_id: int
    function_b_id: int
    similarity: float
    ted_similarity: float
    winnow_similarity: float


class ComparisonSummary(BaseModel):
    """Lightweight comparison listing entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_a_id: int
    submission_b_id: int
    overall_score: float
    created_at: datetime


class ComparisonRead(BaseModel):
    """Full comparison detail with component scores and matches."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_a_id: int
    submission_b_id: int
    overall_score: float
    ted_score: float
    winnow_score: float
    callgraph_score: float
    status: str
    created_at: datetime
    matches: list[FunctionMatchRead]
