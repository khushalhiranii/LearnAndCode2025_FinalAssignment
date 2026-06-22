"""Add notification tables and timesheet freeze columns.

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_profiles",
        sa.Column("timesheet_frozen", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "resource_profiles",
        sa.Column("timesheet_frozen_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "resource_profiles",
        sa.Column("timesheet_frozen_for_week", sa.Date(), nullable=True),
    )

    op.create_table(
        "notification_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("recipient_user_id", sa.BigInteger(), nullable=False),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        sa.Column("reference_key", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column(
            "sent_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "notification_type",
            "recipient_user_id",
            "subject_id",
            "reference_key",
            name="uq_notification_dedup",
        ),
    )

    op.create_table(
        "timesheet_reminder_tracking",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("resource_profile_id", sa.BigInteger(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reminder_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["resource_profile_id"], ["resource_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_profile_id",
            "week_start_date",
            name="uq_timesheet_reminder_week",
        ),
    )


def downgrade() -> None:
    op.drop_table("timesheet_reminder_tracking")
    op.drop_table("notification_log")
    op.drop_column("resource_profiles", "timesheet_frozen_for_week")
    op.drop_column("resource_profiles", "timesheet_frozen_at")
    op.drop_column("resource_profiles", "timesheet_frozen")
