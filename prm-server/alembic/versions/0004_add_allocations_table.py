"""0004 add allocations table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "allocations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "employee_id",
            sa.BigInteger(),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("utilization_percent", sa.Integer(), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="ACTIVE"),
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
    op.create_index("ix_allocations_employee_id", "allocations", ["employee_id"])
    op.create_index("ix_allocations_project_id", "allocations", ["project_id"])
    op.create_index("ix_allocations_status", "allocations", ["status"])
    op.create_index(
        "ix_allocations_employee_status",
        "allocations",
        ["employee_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_allocations_employee_status", table_name="allocations")
    op.drop_index("ix_allocations_status", table_name="allocations")
    op.drop_index("ix_allocations_project_id", table_name="allocations")
    op.drop_index("ix_allocations_employee_id", table_name="allocations")
    op.drop_table("allocations")
