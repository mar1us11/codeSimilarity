"""Comparison and FunctionMatch models: the result of comparing two submissions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class Comparison(TimestampMixin, Base):
    """Aggregated structural-similarity result between two submissions."""

    __tablename__ = "comparisons"
    __table_args__ = (
        UniqueConstraint("submission_a_id", "submission_b_id", name="uq_comparison_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_a_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    submission_b_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    #: Fused overall similarity in [0, 1].
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    #: Component scores, retained for explainability.
    ted_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    winnow_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    callgraph_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")

    matches: Mapped[list[FunctionMatch]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
        order_by="FunctionMatch.similarity.desc()",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"<Comparison id={self.id} "
            f"a={self.submission_a_id} b={self.submission_b_id} "
            f"score={self.overall_score:.3f}>"
        )


class FunctionMatch(Base):
    """A single aligned function pair from the Hopcroft–Karp matching."""

    __tablename__ = "function_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    comparison_id: Mapped[int] = mapped_column(
        ForeignKey("comparisons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    function_a_id: Mapped[int] = mapped_column(
        ForeignKey("function_units.id", ondelete="CASCADE"), nullable=False
    )
    function_b_id: Mapped[int] = mapped_column(
        ForeignKey("function_units.id", ondelete="CASCADE"), nullable=False
    )

    similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ted_similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    winnow_similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    comparison: Mapped[Comparison] = relationship(back_populates="matches")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"<FunctionMatch a={self.function_a_id} b={self.function_b_id} "
            f"sim={self.similarity:.3f}>"
        )
