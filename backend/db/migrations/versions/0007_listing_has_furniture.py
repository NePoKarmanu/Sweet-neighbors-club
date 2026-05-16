"""rename has_repair to has_furniture in listings data

Revision ID: 0007_listing_has_furniture
Revises: 0006_listing_image_url
Create Date: 2026-05-16 00:00:00.000000
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0007_listing_has_furniture"
down_revision = "0006_listing_image_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE listings
        SET data = CASE
            WHEN data ? 'has_repair' THEN (data - 'has_repair') || jsonb_build_object('has_furniture', data->'has_repair')
            ELSE data
        END
        WHERE data IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE listings
        SET data = CASE
            WHEN data ? 'has_furniture' THEN (data - 'has_furniture') || jsonb_build_object('has_repair', data->'has_furniture')
            ELSE data
        END
        WHERE data IS NOT NULL
        """
    )
