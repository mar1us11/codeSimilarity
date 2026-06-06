"""per-browser workspace scoping for submissions

Revision ID: 0004_submission_workspace
Revises: 0003_saved_labs
Create Date: 2026-06-06
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_submission_workspace"
down_revision: str | None = "0003_saved_labs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing rows predate workspaces; park them under a sentinel token so the
    # column can be NOT NULL. They will never match a real browser workspace.
    op.add_column(
        "submissions",
        sa.Column(
            "workspace",
            sa.String(length=64),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.create_index("ix_submissions_workspace", "submissions", ["workspace"])
    # New rows always set the workspace explicitly; drop the backfill default.
    op.alter_column("submissions", "workspace", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_submissions_workspace", table_name="submissions")
    op.drop_column("submissions", "workspace")
