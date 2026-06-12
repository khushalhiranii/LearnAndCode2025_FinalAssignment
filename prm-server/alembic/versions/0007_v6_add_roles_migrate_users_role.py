"""V6: create roles and user_roles tables, migrate users.role data,
then drop users.role enum column and rename is_active → is_account_enabled.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create roles master table ──────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default="true"),
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
    op.create_index("uq_roles_name", "roles", ["name"], unique=True)

    # ── 2. Seed the 3 system roles ────────────────────────────────────────────
    op.execute(
        sa.text(
            """
            INSERT INTO roles (name, description, is_system_role, created_at, updated_at)
            VALUES
              ('ADMIN',    'System administrator — manages users, employees, projects, config', true, NOW(), NOW()),
              ('MANAGER',  'Project and team manager — owns projects, manages allocations',     true, NOW(), NOW()),
              ('EMPLOYEE', 'Individual contributor resource — submits timesheets',              true, NOW(), NOW())
            """
        )
    )

    # ── 3. Create user_roles temporal bridge table ────────────────────────────
    op.create_table(
        "user_roles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            sa.BigInteger(),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=True),          # NULL = currently active
        sa.Column(
            "granted_by_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    # Unique: one grant per (user, role, start date) — prevents duplicate same-day grants
    op.create_index(
        "uq_user_role_from_date",
        "user_roles",
        ["user_id", "role_id", "from_date"],
        unique=True,
    )
    # Partial index: at most one active (NULL to_date) role per user — enforced at app layer,
    # indexed here for fast "current role" lookups
    op.create_index(
        "ix_user_roles_active",
        "user_roles",
        ["user_id"],
        postgresql_where=sa.text("to_date IS NULL"),
    )

    # ── 4. Migrate existing users.role → user_roles ───────────────────────────
    # For every existing user, insert one row with their current role,
    # from_date = their created_at date, to_date = NULL (currently active).
    op.execute(
        sa.text(
            """
            INSERT INTO user_roles (user_id, role_id, from_date, reason, created_at)
            SELECT
                u.id,
                r.id,
                u.created_at::date,
                'Migrated from users.role column during V6 schema upgrade',
                NOW()
            FROM users u
            JOIN roles r ON r.name = u.role
            """
        )
    )

    # ── 5. Drop users.role column (data is now in user_roles) ─────────────────
    op.drop_column("users", "role")

    # ── 6. Rename users.is_active → is_account_enabled ───────────────────────
    op.alter_column("users", "is_active", new_column_name="is_account_enabled")


def downgrade() -> None:
    # Restore is_account_enabled → is_active
    op.alter_column("users", "is_account_enabled", new_column_name="is_active")

    # Re-add role column (populated from user_roles where to_date IS NULL)
    op.add_column("users", sa.Column("role", sa.String(20), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE users u
            SET role = r.name
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = u.id
              AND ur.to_date IS NULL
            """
        )
    )
    op.alter_column("users", "role", nullable=False)

    # Drop user_roles and roles tables
    op.drop_index("ix_user_roles_active", table_name="user_roles")
    op.drop_index("uq_user_role_from_date", table_name="user_roles")
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_table("user_roles")
    op.drop_index("uq_roles_name", table_name="roles")
    op.drop_table("roles")
