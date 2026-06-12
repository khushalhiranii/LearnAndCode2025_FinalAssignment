"""V6: rename employees → resource_profiles, employee_skills → resource_skills,
update all FK column names to match new table names.

Revision ID: 0006
Revises: 0005a
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Rename employees → resource_profiles ──────────────────────────────
    op.rename_table("employees", "resource_profiles")

    # ── 2. Rename is_active → is_available on resource_profiles ──────────────
    op.alter_column("resource_profiles", "is_active", new_column_name="is_available")

    # ── 3. Rename indexes that reference old table name ───────────────────────
    op.drop_index("uq_employees_user_id", table_name="resource_profiles")
    op.create_index(
        "uq_resource_profiles_user_id", "resource_profiles", ["user_id"], unique=True
    )
    op.drop_index("ix_employees_manager_user_id", table_name="resource_profiles")
    op.create_index(
        "ix_resource_profiles_manager_user_id",
        "resource_profiles",
        ["manager_user_id"],
    )

    # ── 4. Rename employee_skills → resource_skills ───────────────────────────
    op.rename_table("employee_skills", "resource_skills")

    # ── 5. Rename employee_id → resource_profile_id in resource_skills ────────
    # Drop composite unique index first (covers renamed column), recreate after
    op.drop_index("uq_employee_skill", table_name="resource_skills")
    op.alter_column(
        "resource_skills", "employee_id", new_column_name="resource_profile_id"
    )
    op.create_index(
        "uq_resource_skill",
        "resource_skills",
        ["resource_profile_id", "skill_id"],
        unique=True,
    )

    # ── 6. Rename employee_id → resource_profile_id in allocations ────────────
    op.drop_index("ix_allocations_employee_id", table_name="allocations")
    op.drop_index("ix_allocations_employee_status", table_name="allocations")
    op.alter_column(
        "allocations", "employee_id", new_column_name="resource_profile_id"
    )
    op.create_index(
        "ix_allocations_resource_profile_id", "allocations", ["resource_profile_id"]
    )
    op.create_index(
        "ix_allocations_resource_profile_status",
        "allocations",
        ["resource_profile_id", "status"],
    )


def downgrade() -> None:
    # Allocations
    op.drop_index("ix_allocations_resource_profile_status", table_name="allocations")
    op.drop_index("ix_allocations_resource_profile_id", table_name="allocations")
    op.alter_column(
        "allocations", "resource_profile_id", new_column_name="employee_id"
    )
    op.create_index("ix_allocations_employee_id", "allocations", ["employee_id"])
    op.create_index(
        "ix_allocations_employee_status", "allocations", ["employee_id", "status"]
    )

    # resource_skills → employee_skills
    op.drop_index("uq_resource_skill", table_name="resource_skills")
    op.alter_column(
        "resource_skills", "resource_profile_id", new_column_name="employee_id"
    )
    op.create_index(
        "uq_employee_skill", "resource_skills", ["employee_id", "skill_id"], unique=True
    )
    op.rename_table("resource_skills", "employee_skills")

    # resource_profiles → employees
    op.drop_index("ix_resource_profiles_manager_user_id", table_name="resource_profiles")
    op.create_index(
        "ix_employees_manager_user_id", "resource_profiles", ["manager_user_id"]
    )
    op.drop_index("uq_resource_profiles_user_id", table_name="resource_profiles")
    op.create_index(
        "uq_employees_user_id", "resource_profiles", ["user_id"], unique=True
    )
    op.alter_column("resource_profiles", "is_available", new_column_name="is_active")
    op.rename_table("resource_profiles", "employees")
