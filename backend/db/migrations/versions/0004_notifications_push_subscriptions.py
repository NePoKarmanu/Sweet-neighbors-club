"""Add push subscriptions and idempotency constraints.

Revision ID: 0004_notif_push_subs
Revises: 0003_listing_missing_runs_count
Create Date: 2026-05-02 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_notif_push_subs"
down_revision: Union[str, Sequence[str], None] = "0003_listing_missing_runs_count"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("p256dh", sa.String(length=512), nullable=False),
        sa.Column("auth", sa.String(length=512), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
    )
    op.create_unique_constraint(
        "uq_notifications_user_listing",
        "notifications",
        ["user_id", "listing_id"],
    )
    op.create_unique_constraint(
        "uq_sent_listings_user_listing",
        "sent_listings",
        ["user_id", "listing_id"],
    )
    op.create_unique_constraint(
        "uq_notification_deliveries_notification_channel",
        "notification_deliveries",
        ["notification_id", "channel"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_sent_listings_user_listing", "sent_listings", type_="unique")
    op.drop_constraint("uq_notifications_user_listing", "notifications", type_="unique")
    op.drop_constraint(
        "uq_notification_deliveries_notification_channel",
        "notification_deliveries",
        type_="unique",
    )
    op.drop_table("push_subscriptions")
