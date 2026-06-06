"""Persistence for comparisons and their function matches."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.comparison import Comparison
from app.repositories.base import BaseRepository


class ComparisonRepository(BaseRepository[Comparison]):
    """Read/write access to :class:`Comparison` aggregates."""

    model = Comparison

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_with_matches(self, comparison_id: int) -> Comparison | None:
        stmt = (
            select(Comparison)
            .where(Comparison.id == comparison_id)
            .options(selectinload(Comparison.matches))
        )
        return self.session.scalars(stmt).one_or_none()

    def find_pair(self, submission_a_id: int, submission_b_id: int) -> Comparison | None:
        """Return an existing comparison for the (unordered) pair, if any."""
        stmt = select(Comparison).where(
            or_(
                (Comparison.submission_a_id == submission_a_id)
                & (Comparison.submission_b_id == submission_b_id),
                (Comparison.submission_a_id == submission_b_id)
                & (Comparison.submission_b_id == submission_a_id),
            )
        )
        return self.session.scalars(stmt).first()

    def list_for_submission(self, submission_id: int) -> list[Comparison]:
        stmt = (
            select(Comparison)
            .where(
                or_(
                    Comparison.submission_a_id == submission_id,
                    Comparison.submission_b_id == submission_id,
                )
            )
            .order_by(Comparison.overall_score.desc())
        )
        return list(self.session.scalars(stmt).all())
