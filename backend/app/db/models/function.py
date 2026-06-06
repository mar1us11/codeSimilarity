"""FunctionUnit model: a single normalized function extracted from a submission.

Each function carries the structural artifacts the algorithms consume:
* the normalized AST (serialized) for Tree Edit Distance,
* the winnowing fingerprint set for Jaccard similarity,
* call-graph metadata (callee names) for graph analysis.

Storing these means a submission is parsed and normalized exactly once; every
pairwise comparison then reuses the cached artifacts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.submission import Submission


class FunctionUnit(Base):
    """A normalized function and its precomputed structural artifacts."""

    __tablename__ = "function_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    #: Original identifier (kept only for display; never used in comparison).
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    #: Position in the source file. Comparison is order-independent, so this is
    #: purely informational.
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    #: Count of nodes in the normalized AST (drives TED normalization).
    ast_node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    #: Serialized normalized AST (see app.parsing.ast_nodes.ASTNode.to_dict()).
    normalized_ast: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    #: Winnowing fingerprints (set of 64-bit hashes stored as a sorted list).
    #: BIGINT (not INTEGER): the hashes are taken mod (1<<61)-1, well beyond the
    #: 32-bit INTEGER range.
    fingerprints: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), nullable=False, default=list
    )

    #: Normalized names of functions this function calls (call-graph edges).
    callees: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    submission: Mapped[Submission] = relationship(back_populates="functions")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<FunctionUnit id={self.id} name={self.name!r} nodes={self.ast_node_count}>"
