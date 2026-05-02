"""Add unique listing external id per aggregator.

Revision ID: 0002_listing_unique_extid
Revises: 0001_initial_schema
Create Date: 2026-05-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0002_listing_unique_extid"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_listings_aggregator_external_id",
        "listings",
        ["aggregator_id", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_listings_aggregator_external_id",
        "listings",
        type_="unique",
    )
