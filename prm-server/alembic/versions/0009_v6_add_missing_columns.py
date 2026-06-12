"""V6: add missing columns identified in ER discrepancy review —
skills.is_active (soft-delete support) and milestones.completed_date
(needed by scheduler to detect late completions).

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── skills.is_active ──────────────────────────────────────────────────────
    # Allows soft-deactivation of obsolete skills while preserving historical
    # resource_skills rows (RESTRICT FK prevents hard delete).
    op.add_column(
        "skills",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    op.create_index("ix_skills_is_active", "skills", ["is_active"])

    # ── milestones.completed_date ─────────────────────────────────────────────
    # Set automatically by MilestoneUseCase when status transitions to DONE.
    # Cleared when status transitions away from DONE.
    # Used by the scheduler (RecomputeProjectHealth) to detect late completions.
    op.add_column(
        "milestones",
        sa.Column("completed_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("milestones", "completed_date")
    op.drop_index("ix_skills_is_active", table_name="skills")
    op.drop_column("skills", "is_active")
