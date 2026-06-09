"""0002 add employees and skills tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # skills master table
    op.create_table(
        "skills",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("uq_skills_name", "skills", ["name"], unique=True)

    # employees table
    op.create_table(
        "employees",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("date_of_joining", sa.Date(), nullable=True),
        sa.Column("manager_user_id", sa.BigInteger(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("uq_employees_user_id", "employees", ["user_id"], unique=True)
    op.create_index("ix_employees_manager_user_id", "employees", ["manager_user_id"])

    # employee_skills associative table
    op.create_table(
        "employee_skills",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.BigInteger(),
                  sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.BigInteger(),
                  sa.ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proficiency", sa.String(20), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index(
        "uq_employee_skill", "employee_skills",
        ["employee_id", "skill_id"], unique=True
    )


def downgrade() -> None:
    op.drop_table("employee_skills")
    op.drop_index("ix_employees_manager_user_id", table_name="employees")
    op.drop_index("uq_employees_user_id", table_name="employees")
    op.drop_table("employees")
    op.drop_index("uq_skills_name", table_name="skills")
    op.drop_table("skills")
