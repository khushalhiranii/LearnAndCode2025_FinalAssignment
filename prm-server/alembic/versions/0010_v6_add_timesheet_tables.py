"""Sprint 5 / V6: create timesheet, timesheet_entry, activity_tag,
and timesheet_entry_activity_tag tables.

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── timesheets ────────────────────────────────────────────────────────────
    op.create_table(
        "timesheets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "resource_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("resource_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column(
            "total_hours",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status",
            sa.String(10),
            nullable=False,
            comment="SUBMITTED | MISSED",
        ),
        sa.Column(
            "submitted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    # BRD Rule 10: duplicate submission for same resource + week rejected at DB level
    op.create_index(
        "uq_timesheets_resource_week",
        "timesheets",
        ["resource_profile_id", "week_start_date"],
        unique=True,
    )
    op.create_index(
        "ix_timesheets_resource_profile_id", "timesheets", ["resource_profile_id"]
    )
    op.create_index("ix_timesheets_status", "timesheets", ["status"])

    # ── timesheet_entries ─────────────────────────────────────────────────────
    op.create_table(
        "timesheet_entries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "timesheet_id",
            sa.BigInteger(),
            sa.ForeignKey("timesheets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hours_worked",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_timesheet_entries_timesheet_id", "timesheet_entries", ["timesheet_id"]
    )
    op.create_index(
        "ix_timesheet_entries_project_id", "timesheet_entries", ["project_id"]
    )

    # ── activity_tags ─────────────────────────────────────────────────────────
    op.create_table(
        "activity_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column(
            "is_system_tag",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    op.create_index("uq_activity_tags_name", "activity_tags", ["name"], unique=True)
    op.create_index("ix_activity_tags_is_active", "activity_tags", ["is_active"])

    # ── timesheet_entry_activity_tags (junction) ───────────────────────────────
    op.create_table(
        "timesheet_entry_activity_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "timesheet_entry_id",
            sa.BigInteger(),
            sa.ForeignKey("timesheet_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "activity_tag_id",
            sa.BigInteger(),
            sa.ForeignKey("activity_tags.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Populated only when activity_tag.category = 'OTHER'
        sa.Column("custom_tag_text", sa.String(200), nullable=True),
    )
    op.create_index(
        "ix_teat_timesheet_entry_id",
        "timesheet_entry_activity_tags",
        ["timesheet_entry_id"],
    )


def downgrade() -> None:
    op.drop_table("timesheet_entry_activity_tags")
    op.drop_index("ix_activity_tags_is_active", table_name="activity_tags")
    op.drop_index("uq_activity_tags_name", table_name="activity_tags")
    op.drop_table("activity_tags")
    op.drop_index("ix_timesheet_entries_project_id", table_name="timesheet_entries")
    op.drop_index("ix_timesheet_entries_timesheet_id", table_name="timesheet_entries")
    op.drop_table("timesheet_entries")
    op.drop_index("ix_timesheets_status", table_name="timesheets")
    op.drop_index("ix_timesheets_resource_profile_id", table_name="timesheets")
    op.drop_index("uq_timesheets_resource_week", table_name="timesheets")
    op.drop_table("timesheets")
