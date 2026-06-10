"""Rename EXPERT -> ADVANCED in employee_skills and PENDING -> NOT_STARTED in milestones.

Revision ID: 0005a
Revises: 0004
Create Date: 2026-06-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005a"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix 3: rename proficiency EXPERT -> ADVANCED (BRD Screen 3.1.3 + UML)
    op.execute(
        sa.text(
            "UPDATE employee_skills SET proficiency = 'ADVANCED' "
            "WHERE proficiency = 'EXPERT'"
        )
    )

    # Fix 4: rename milestone status PENDING -> NOT_STARTED (BRD Screen 3.2.4 + UML)
    op.execute(
        sa.text(
            "UPDATE milestones SET status = 'NOT_STARTED' "
            "WHERE status = 'PENDING'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE milestones SET status = 'PENDING' "
            "WHERE status = 'NOT_STARTED'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE employee_skills SET proficiency = 'EXPERT' "
            "WHERE proficiency = 'ADVANCED'"
        )
    )
