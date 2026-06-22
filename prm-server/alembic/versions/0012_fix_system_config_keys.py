"""Fix system_config keys for LLM and scheduler settings.

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Rename ai_provider -> llm_provider if present
    conn.execute(
        sa.text(
            """
            UPDATE system_config
            SET config_key = 'llm_provider'
            WHERE config_key = 'ai_provider'
            """
        )
    )

    defaults = [
        ("llm_provider", "gemma"),
        ("llm_api_key", ""),
        ("llm_base_url", ""),
        ("llm_model", ""),
        ("scheduler_interval_minutes", "240"),
        ("max_weekly_hours", "40"),
    ]
    for key, value in defaults:
        conn.execute(
            sa.text(
                """
                INSERT INTO system_config (config_key, config_value, updated_at)
                SELECT CAST(:key AS VARCHAR(100)), CAST(:value AS TEXT), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM system_config
                    WHERE config_key = CAST(:key AS VARCHAR(100))
                )
                """
            ),
            {"key": key, "value": value},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for key in ("llm_base_url", "llm_model", "scheduler_interval_minutes"):
        conn.execute(
            sa.text(
                "DELETE FROM system_config WHERE config_key = CAST(:key AS VARCHAR(100))"
            ),
            {"key": key},
        )
    conn.execute(
        sa.text(
            """
            UPDATE system_config
            SET config_key = 'ai_provider'
            WHERE config_key = 'llm_provider'
            """
        )
    )
