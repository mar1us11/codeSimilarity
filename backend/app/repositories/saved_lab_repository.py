"""Persistence access for saved score sets (repository pattern)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.saved_lab import SavedLab


class SavedLabRepository:
    """Reads and writes :class:`SavedLab` records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, lab: SavedLab) -> SavedLab:
        self._session.add(lab)
        self._session.flush()
        return lab

    def get_by_label(self, label: str) -> SavedLab | None:
        """Look a lab up by name, case-insensitively (names are unique)."""
        stmt = select(SavedLab).where(func.lower(SavedLab.label) == label.strip().lower())
        return self._session.scalars(stmt).one_or_none()

    def get(self, lab_id: int) -> SavedLab | None:
        return self._session.get(SavedLab, lab_id)
