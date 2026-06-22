"""Clear hardcoded Gemma URL/model from existing system_config rows.

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

_LEGACY_BASE_URL = "http://164.52.211.238/api/generate"
_LEGACY_MODEL = "gemma3:12b-it-q8_0"


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE system_config
            SET config_value = ''
            WHERE config_key = 'llm_base_url'
              AND config_value = :legacy_url
            """
        ),
        {"legacy_url": _LEGACY_BASE_URL},
    )
    conn.execute(
        sa.text(
            """
            UPDATE system_config
            SET config_value = ''
            WHERE config_key = 'llm_model'
              AND config_value = :legacy_model
            """
        ),
        {"legacy_model": _LEGACY_MODEL},
    )


def downgrade() -> None:
    pass
