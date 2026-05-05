"""add image_url to listings

Revision ID: 0006_listing_image_url
Revises: 0005_listing_city_column
Create Date: 2026-05-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_listing_image_url"
down_revision = "0005_listing_city_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("image_url", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("listings", "image_url")
