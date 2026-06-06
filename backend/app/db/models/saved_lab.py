"""SavedLab model: a password-protected snapshot of an analysis report.

When an instructor finishes a cohort analysis they may persist the resulting
similarity scores behind a password. The full :class:`AnalysisReport` is stored
verbatim as JSONB so it can be re-opened later without re-running the pipeline
(submissions may even have been deleted in the meantime).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SavedLab(TimestampMixin, Base):
    """A saved, password-protected analysis report ("lab")."""

    __tablename__ = "saved_labs"

    id: Mapped[int] = mapped_column(primary_key=True)
    #: Human-friendly label shown in the locked list (e.g. "Lab 3 — Week 12").
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    #: PBKDF2 hash of the access password (see app.core.security).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    #: The full AnalysisReport, serialized with model_dump(mode="json").
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<SavedLab id={self.id} label={self.label!r}>"
