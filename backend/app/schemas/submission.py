"""Submission request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    """Payload for registering a new submission."""

    name: str = Field(min_length=1, max_length=255, description="Display name / author.")
    filename: str = Field(min_length=1, max_length=512)
    source_code: str = Field(min_length=1, description="Raw C source code.")


class FunctionRead(BaseModel):
    """A normalized function as exposed by the API."""

    id: int
    name: str
    order_index: int
    ast_node_count: int
    fingerprint_count: int

    @classmethod
    def from_model(cls, function: object) -> FunctionRead:
        fingerprints = getattr(function, "fingerprints", None) or []
        return cls(
            id=function.id,  # type: ignore[attr-defined]
            name=function.name,  # type: ignore[attr-defined]
            order_index=function.order_index,  # type: ignore[attr-defined]
            ast_node_count=function.ast_node_count,  # type: ignore[attr-defined]
            fingerprint_count=len(fingerprints),
        )


class SubmissionSummary(BaseModel):
    """Lightweight submission listing entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    filename: str
    language: str
    ast_node_count: int
    function_count: int
    created_at: datetime


class SubmissionRead(BaseModel):
    """Full submission detail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    filename: str
    language: str
    ast_node_count: int
    created_at: datetime
    functions: list[FunctionRead]
