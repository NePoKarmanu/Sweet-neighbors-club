"""Add missing runs counter for listing staleness.

Revision ID: 0003_listing_missing_runs_count
Revises: 0002_listing_unique_extid
Create Date: 2026-05-02 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_listing_missing_runs_count"
down_revision: Union[str, Sequence[str], None] = "0002_listing_unique_extid"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("missing_runs_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("listings", "missing_runs_count")
