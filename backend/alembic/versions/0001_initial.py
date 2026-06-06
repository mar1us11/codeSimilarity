"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-30
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("ast_node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "function_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ast_node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("normalized_ast", postgresql.JSONB(), nullable=False),
        sa.Column(
            "fingerprints",
            postgresql.ARRAY(sa.BigInteger()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "callees",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"], ["submissions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_function_units_submission_id", "function_units", ["submission_id"]
    )

    op.create_table(
        "comparisons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_a_id", sa.Integer(), nullable=False),
        sa.Column("submission_b_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ted_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("winnow_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("callgraph_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["submission_a_id"], ["submissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["submission_b_id"], ["submissions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "submission_a_id", "submission_b_id", name="uq_comparison_pair"
        ),
    )
    op.create_index(
        "ix_comparisons_submission_a_id", "comparisons", ["submission_a_id"]
    )
    op.create_index(
        "ix_comparisons_submission_b_id", "comparisons", ["submission_b_id"]
    )

    op.create_table(
        "function_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comparison_id", sa.Integer(), nullable=False),
        sa.Column("function_a_id", sa.Integer(), nullable=False),
        sa.Column("function_b_id", sa.Integer(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ted_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.Column("winnow_similarity", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["comparisons.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["function_a_id"], ["function_units.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["function_b_id"], ["function_units.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_function_matches_comparison_id", "function_matches", ["comparison_id"]
    )


def downgrade() -> None:
    op.drop_table("function_matches")
    op.drop_table("comparisons")
    op.drop_table("function_units")
    op.drop_table("submissions")
