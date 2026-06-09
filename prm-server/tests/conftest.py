"""
Shared fixtures for the entire test suite.

Unit test fixtures use InMemoryUserRepository — no database required.
Integration test fixtures use a real PostgreSQL instance via TEST_DATABASE_URL.
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.ports.repositories import IUserRepository
from src.infrastructure.security.password_hasher import hash_password


# ── In-memory fake repository (unit tests) ───────────────────────────────────


class InMemoryUserRepository(IUserRepository):
    """Fake repository — no DB required. Satisfies IUserRepository (LSP)."""

    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._by_username: dict[str, int] = {}
        self._next_id = 1

    async def find_by_username(self, username: str) -> User | None:
        uid = self._by_username.get(username)
        return self._store.get(uid) if uid else None

    async def find_by_id(self, user_id: int) -> User | None:
        return self._store.get(user_id)

    async def save(self, user: User) -> User:
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
        self._store[user.id] = user
        self._by_username[user.username] = user.id
        return user

    async def update_password(
        self,
        user_id: int,
        new_password_hash: str,
        force_password_change: bool,
    ) -> None:
        user = self._store[user_id]
        user.password_hash = new_password_hash
        user.force_password_change = force_password_change


def make_admin_user(
    force_password_change: bool = False,
    is_active: bool = True,
    plain_password: str = "Admin@1234",
) -> User:
    return User(
        id=1,
        full_name="System Administrator",
        email="admin@prm.local",
        username="admin",
        password_hash=hash_password(plain_password),
        role=Role.ADMIN,
        is_active=is_active,
        force_password_change=force_password_change,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def fake_user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest_asyncio.fixture
async def active_admin_user(fake_user_repo: InMemoryUserRepository) -> InMemoryUserRepository:
    """Repo seeded with an admin whose force_password_change=False."""
    user = make_admin_user(force_password_change=False)
    await fake_user_repo.save(user)
    return fake_user_repo


@pytest_asyncio.fixture
async def force_change_admin(fake_user_repo: InMemoryUserRepository) -> InMemoryUserRepository:
    """Repo seeded with an admin whose force_password_change=True."""
    user = make_admin_user(force_password_change=True)
    await fake_user_repo.save(user)
    return fake_user_repo


@pytest_asyncio.fixture
async def inactive_admin(fake_user_repo: InMemoryUserRepository) -> InMemoryUserRepository:
    """Repo seeded with a deactivated admin."""
    user = make_admin_user(is_active=False)
    await fake_user_repo.save(user)
    return fake_user_repo


# ── Integration test fixtures (real DB) ──────────────────────────────────────


@pytest_asyncio.fixture
async def seeded_admin_client():
    """
    Brings up a clean test database, applies migrations, seeds the admin,
    and yields an httpx AsyncClient pointed at the FastAPI app.

    Requires TEST_DATABASE_URL (or falls back to DATABASE_URL from .env).
    Run the Docker DB before executing integration tests:
        docker-compose -f docker/docker-compose.yml up -d db
    """
    import os
    import subprocess

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine

    from src.infrastructure.database.engine import Base
    from src.main import app
    from seeds.seed_admin import seed

    test_db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://prm_user:prm_pass@localhost:5432/prm_db",
    )
    os.environ["DATABASE_URL"] = test_db_url

    # Apply migrations
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    # Seed admin
    await seed()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Teardown — drop all tables for a clean state next run
    engine = create_async_engine(test_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
