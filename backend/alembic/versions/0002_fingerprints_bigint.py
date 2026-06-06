"""widen function_units.fingerprints to BIGINT[]

Winnowing hashes are taken mod (1<<61)-1, which overflows 32-bit INTEGER.
Store them as BIGINT[] instead.

Revision ID: 0002_fingerprints_bigint
Revises: 0001_initial
Create Date: 2026-06-04
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_fingerprints_bigint"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE function_units "
        "ALTER COLUMN fingerprints TYPE BIGINT[] "
        "USING fingerprints::BIGINT[]"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE function_units "
        "ALTER COLUMN fingerprints TYPE INTEGER[] "
        "USING fingerprints::INTEGER[]"
    )
