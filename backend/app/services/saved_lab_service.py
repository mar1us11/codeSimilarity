"""Service for saving and reopening password-protected analysis reports."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models.saved_lab import SavedLab
from app.repositories.saved_lab_repository import SavedLabRepository
from app.schemas.analysis import AnalysisReport
from app.schemas.saved_lab import SavedLabSummary


class DuplicateLabNameError(ValueError):
    """Raised when a saved score set already uses the requested name."""


class InvalidLabCredentialsError(PermissionError):
    """Raised when no saved score set matches the supplied name + password.

    Deliberately does not distinguish "unknown name" from "wrong password" so a
    caller cannot probe which lab names exist.
    """


class SavedLabService:
    """Persists analysis reports behind a name + password and reopens them."""

    def __init__(self, session: Session) -> None:
        self._repo = SavedLabRepository(session)

    def save(self, label: str, password: str, report: AnalysisReport) -> SavedLabSummary:
        """Store ``report`` under the unique name ``label`` behind ``password``.

        Raises:
            DuplicateLabNameError: if the name is already taken.
        """
        name = (label or "").strip()
        if name == "":
            raise DuplicateLabNameError("A lab name is required.")
        if self._repo.get_by_label(name) is not None:
            raise DuplicateLabNameError(f'The name "{name}" is already taken.')

        lab = SavedLab(
            label=name,
            password_hash=hash_password(password),
            report=report.model_dump(mode="json"),
        )
        try:
            self._repo.add(lab)
        except IntegrityError as exc:  # lost a race against the unique index
            raise DuplicateLabNameError(f'The name "{name}" is already taken.') from exc
        return self.to_summary(lab)

    def unlock_by_name(self, name: str, password: str) -> AnalysisReport:
        """Return the full report whose name + password both match."""
        lab = self._repo.get_by_label(name)
        if lab is None or not verify_password(password, lab.password_hash):
            raise InvalidLabCredentialsError()
        return AnalysisReport.model_validate(lab.report)

    @staticmethod
    def to_summary(lab: SavedLab) -> SavedLabSummary:
        report = lab.report or {}
        return SavedLabSummary(
            id=lab.id,
            label=lab.label,
            created_at=lab.created_at,
            submission_count=int(report.get("submission_count", 0)),
            highest_student_score=float(report.get("highest_student_score", 0.0)),
        )
