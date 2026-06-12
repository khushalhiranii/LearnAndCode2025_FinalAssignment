"""
Bootstrap the first Admin account.

Usage (run from prm-server/ directory):
    python seeds/seed_admin.py

Default credentials:  admin / Admin@1234
The admin is forced to change this password on first login.
Rule: idempotent — checks for existing admin before inserting.
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Make src importable when run from repo root or prm-server/
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.domain.enums import Role
from src.infrastructure.database.models.role_model import RoleModel, UserRoleModel
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.security.password_hasher import hash_password


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )

    async with factory() as session:
        existing = await session.execute(
            select(UserModel).where(
                UserModel.username == settings.admin_default_username
            )
        )
        if existing.scalar_one_or_none() is not None:
            print(
                f"[seed_admin] Admin '{settings.admin_default_username}' already exists."
                " Skipping."
            )
            await engine.dispose()
            return

        admin = UserModel()
        admin.full_name = settings.admin_default_full_name
        admin.email = settings.admin_default_email
        admin.username = settings.admin_default_username
        admin.password_hash = hash_password(settings.admin_default_password)
        admin.is_account_enabled = True
        admin.force_password_change = True

        session.add(admin)
        await session.flush()  # populate admin.id before using as FK

        # Lookup ADMIN role from roles table (seeded by migration 0007)
        role_result = await session.execute(
            select(RoleModel).where(RoleModel.name == Role.ADMIN.value)
        )
        admin_role = role_result.scalar_one_or_none()
        if admin_role is None:
            print("[seed_admin] ERROR: ADMIN role not found in roles table. Run migrations first.")
            await session.rollback()
            await engine.dispose()
            return

        user_role = UserRoleModel()
        user_role.user_id = admin.id
        user_role.role_id = admin_role.id
        user_role.from_date = date.today()
        user_role.to_date = None  # active indefinitely
        user_role.granted_by_user_id = None  # self-seeded
        user_role.reason = "Initial admin seed"

        session.add(user_role)
        await session.commit()
        print(
            f"[seed_admin] Admin '{settings.admin_default_username}' created."
            " Change password on first login."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
