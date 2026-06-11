"""V6: create system_config, project_health_snapshots, and ai_suggestion_audit tables.
These complete the full V6 ER diagram schema.

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── system_config ─────────────────────────────────────────────────────────
    # Runtime key-value settings managed by Admin (UC17 Configure System).
    # Key example: max_weekly_hours = "40"
    op.create_table(
        "system_config",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("config_key", sa.String(100), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column(
            "updated_by_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("uq_system_config_key", "system_config", ["config_key"], unique=True)

    # Seed default system config values
    op.execute(
        sa.text(
            """
            INSERT INTO system_config (config_key, config_value, updated_at)
            VALUES
              ('max_weekly_hours', '40', NOW()),
              ('ai_provider',      'openai', NOW())
            """
        )
    )

    # ── project_health_snapshots ──────────────────────────────────────────────
    # Computed by the Scheduler (UC32 Recompute Project Health).
    # One row per scheduler run per project — historical series, never updated.
    op.create_table(
        "project_health_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "health_status",
            sa.String(15),
            nullable=False,
            comment="ON_TRACK | ATTENTION | AT_RISK",
        ),
        sa.Column("risk_flags_json", sa.Text(), nullable=True),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_project_health_snapshots_project_id",
        "project_health_snapshots",
        ["project_id"],
    )
    op.create_index(
        "ix_project_health_snapshots_computed_at",
        "project_health_snapshots",
        ["computed_at"],
    )

    # ── ai_suggestion_audit ───────────────────────────────────────────────────
    # Immutable audit log of every AI request (SKILL_MATCH, RISK_SUMMARY).
    # subject_id references projects.id for both current request types.
    op.create_table(
        "ai_suggestion_audit",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "request_type",
            sa.String(20),
            nullable=False,
            comment="SKILL_MATCH | RISK_SUMMARY",
        ),
        sa.Column(
            "subject_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
            comment="project_id for both current request types",
        ),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_ai_suggestion_audit_subject_id", "ai_suggestion_audit", ["subject_id"]
    )
    op.create_index(
        "ix_ai_suggestion_audit_request_type",
        "ai_suggestion_audit",
        ["request_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_suggestion_audit_request_type", table_name="ai_suggestion_audit")
    op.drop_index("ix_ai_suggestion_audit_subject_id", table_name="ai_suggestion_audit")
    op.drop_table("ai_suggestion_audit")

    op.drop_index(
        "ix_project_health_snapshots_computed_at", table_name="project_health_snapshots"
    )
    op.drop_index(
        "ix_project_health_snapshots_project_id", table_name="project_health_snapshots"
    )
    op.drop_table("project_health_snapshots")

    op.drop_index("uq_system_config_key", table_name="system_config")
    op.drop_table("system_config")
