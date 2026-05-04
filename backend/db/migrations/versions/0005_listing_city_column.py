"""Add city column to listings.

Revision ID: 0005_listing_city_column
Revises: 0004_notif_push_subs
Create Date: 2026-05-02 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_listing_city_column"
down_revision: Union[str, Sequence[str], None] = "0004_notif_push_subs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("city", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("listings", "city")
