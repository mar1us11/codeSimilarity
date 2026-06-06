"""Persistence for submissions and their function units."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.function import FunctionUnit
from app.db.models.submission import Submission
from app.repositories.base import BaseRepository


class SubmissionRepository(BaseRepository[Submission]):
    """Read/write access to :class:`Submission` aggregates."""

    model = Submission

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_with_functions(
        self, submission_id: int, *, workspace: str | None = None
    ) -> Submission | None:
        stmt = (
            select(Submission)
            .where(Submission.id == submission_id)
            .options(selectinload(Submission.functions))
        )
        if workspace is not None:
            stmt = stmt.where(Submission.workspace == workspace)
        return self.session.scalars(stmt).one_or_none()

    def list_with_counts(
        self, *, workspace: str, limit: int = 100, offset: int = 0
    ) -> list[Submission]:
        stmt = (
            select(Submission)
            .where(Submission.workspace == workspace)
            .options(selectinload(Submission.functions))
            .order_by(Submission.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())

    def add_function(self, function: FunctionUnit) -> FunctionUnit:
        self.session.add(function)
        self.session.flush()
        return function
