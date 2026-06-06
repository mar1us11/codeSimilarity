"""Submission model: one uploaded C source file."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.function import FunctionUnit


class Submission(TimestampMixin, Base):
    """A single C assignment submitted for analysis."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    #: Per-browser workspace token (sessionStorage). Submissions are private to
    #: the browser tab that created them; there are no user accounts.
    workspace: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="c")
    source_code: Mapped[str] = mapped_column(Text, nullable=False)

    #: Number of structural AST nodes across all functions (cached for ranking).
    ast_node_count: Mapped[int] = mapped_column(default=0, nullable=False)

    functions: Mapped[list[FunctionUnit]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="FunctionUnit.order_index",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Submission id={self.id} name={self.name!r} functions={len(self.functions)}>"
