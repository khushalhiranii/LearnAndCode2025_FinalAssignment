"""
Seed default activity tags for timesheet entry tagging.

Usage (run from prm-server/ directory):
    python seeds/seed_activity_tags.py

Idempotent — skips tags that already exist by name.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.infrastructure.database.models.timesheet_model import ActivityTagModel

DEFAULT_TAGS: list[tuple[str, str, bool]] = [
    ("Development", "DEVELOPMENT", True),
    ("Code Review", "REVIEW", True),
    ("Meeting", "MEETING", True),
    ("Testing", "TESTING", True),
    ("Documentation", "DOCUMENTATION", True),
    ("Other", "OTHER", True),
]


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )

    async with factory() as session:
        for name, category, is_system in DEFAULT_TAGS:
            existing = await session.execute(
                select(ActivityTagModel).where(ActivityTagModel.name == name)
            )
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                ActivityTagModel(
                    name=name,
                    category=category,
                    is_system_tag=is_system,
                    is_active=True,
                )
            )
        await session.commit()
        print(f"[seed_activity_tags] Ensured {len(DEFAULT_TAGS)} default tags exist.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
