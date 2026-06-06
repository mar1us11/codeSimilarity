"""enforce case-insensitive unique saved-lab names

Reopening a saved score set is done by typing its name + password (there is no
browsable list), so the name must identify exactly one lab.

Revision ID: 0005_unique_lab_name
Revises: 0004_submission_workspace
Create Date: 2026-06-06
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_unique_lab_name"
down_revision: str | None = "0004_submission_workspace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_saved_labs_label_lower",
        "saved_labs",
        [sa.text("lower(label)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_saved_labs_label_lower", table_name="saved_labs")
