"""V6: create resource_hierarchy closure table for scalable org-tree queries.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── resource_hierarchy closure table ─────────────────────────────────────
    # Stores all ancestor→descendant paths in the reporting tree.
    # Every resource has a self-row (ancestor_id = descendant_id, depth = 0).
    # Maintained by the application layer on every manager_user_id change.
    op.create_table(
        "resource_hierarchy",
        sa.Column(
            "ancestor_id",
            sa.BigInteger(),
            sa.ForeignKey("resource_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "descendant_id",
            sa.BigInteger(),
            sa.ForeignKey("resource_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "depth",
            sa.Integer(),
            nullable=False,
            comment="0 = self-row, 1 = direct report, n = nth level",
        ),
    )
    # Unique: one path per (ancestor, descendant) pair
    op.create_index(
        "uq_resource_hierarchy",
        "resource_hierarchy",
        ["ancestor_id", "descendant_id"],
        unique=True,
    )
    # Fast lookup: all descendants of an ancestor (dashboard drill-down)
    op.create_index(
        "ix_resource_hierarchy_ancestor", "resource_hierarchy", ["ancestor_id"]
    )
    # Fast lookup: all ancestors of a descendant (upward org path)
    op.create_index(
        "ix_resource_hierarchy_descendant", "resource_hierarchy", ["descendant_id"]
    )

    # ── Seed self-rows for all existing resource profiles ─────────────────────
    op.execute(
        sa.text(
            """
            INSERT INTO resource_hierarchy (ancestor_id, descendant_id, depth)
            SELECT id, id, 0
            FROM resource_profiles
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_resource_hierarchy_descendant", table_name="resource_hierarchy")
    op.drop_index("ix_resource_hierarchy_ancestor", table_name="resource_hierarchy")
    op.drop_index("uq_resource_hierarchy", table_name="resource_hierarchy")
    op.drop_table("resource_hierarchy")
