"""
Shared fixtures for the entire test suite.

Unit test fixtures use InMemoryUserRepository — no database required.
Integration test fixtures use a real PostgreSQL instance via TEST_DATABASE_URL.
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from src.domain.entities.employee import Employee
from src.domain.entities.allocation import Allocation
from src.domain.entities.milestone import Milestone
from src.domain.entities.project import Project
from src.domain.entities.skill import EmployeeSkill, Skill
from src.domain.entities.user import User
from src.domain.enums import AllocationStatus, MilestoneStatus, ProficiencyLevel, ProjectStatus, Role
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    IMilestoneRepository,
    IProjectRepository,
    ISkillRepository,
    IUserRepository,
)
from src.infrastructure.security.password_hasher import hash_password


# ── In-memory fake repositories (unit tests) ─────────────────────────────────


class InMemoryUserRepository(IUserRepository):
    """Fake repository — no DB required. Satisfies IUserRepository (LSP)."""

    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._by_username: dict[str, int] = {}
        self._by_email: dict[str, int] = {}
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
        else:
            # Advance counter so auto-assigned IDs don't collide with pre-set ones
            self._next_id = max(self._next_id, user.id + 1)
        self._store[user.id] = user
        self._by_username[user.username] = user.id
        self._by_email[user.email] = user.id
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

    async def find_all(
        self,
        role: Role | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        users = list(self._store.values())
        if role is not None:
            users = [u for u in users if u.role == role]
        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]
        total = len(users)
        start = (page - 1) * page_size
        return users[start: start + page_size], total

    async def find_by_email(self, email: str) -> User | None:
        uid = self._by_email.get(email)
        return self._store.get(uid) if uid else None

    async def update_active(self, user_id: int, is_active: bool) -> None:
        if user_id in self._store:
            self._store[user_id].is_active = is_active


class InMemoryEmployeeRepository(IEmployeeRepository):
    """Fake employee repository for unit tests."""

    def __init__(self) -> None:
        self._store: dict[int, Employee] = {}
        self._by_user: dict[int, int] = {}
        self._skills: dict[int, EmployeeSkill] = {}  # employee_skill_id → EmployeeSkill
        self._next_id = 1
        self._next_skill_id = 1

    async def find_by_id(self, employee_id: int) -> Employee | None:
        return self._store.get(employee_id)

    async def find_by_user_id(self, user_id: int) -> Employee | None:
        eid = self._by_user.get(user_id)
        return self._store.get(eid) if eid else None

    async def find_all(
        self,
        is_active: bool | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        items = list(self._store.values())
        if is_active is not None:
            items = [e for e in items if e.is_active == is_active]
        if manager_user_id is not None:
            items = [e for e in items if e.manager_user_id == manager_user_id]
        total = len(items)
        start = (page - 1) * page_size
        return items[start: start + page_size], total

    async def save(self, employee: Employee) -> Employee:
        if employee.id is None:
            employee.id = self._next_id
            self._next_id += 1
        self._store[employee.id] = employee
        self._by_user[employee.user_id] = employee.id
        return employee

    async def update_active(self, employee_id: int, is_active: bool) -> None:
        if employee_id in self._store:
            self._store[employee_id].is_active = is_active

    async def update_manager(
        self, employee_id: int, manager_user_id: int | None
    ) -> None:
        if employee_id in self._store:
            self._store[employee_id].manager_user_id = manager_user_id

    async def find_skills(self, employee_id: int) -> list[EmployeeSkill]:
        return [s for s in self._skills.values() if s.employee_id == employee_id]

    async def find_employee_skill(
        self, employee_id: int, skill_id: int
    ) -> EmployeeSkill | None:
        for s in self._skills.values():
            if s.employee_id == employee_id and s.skill_id == skill_id:
                return s
        return None

    async def add_skill(
        self,
        employee_id: int,
        skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> EmployeeSkill:
        now = datetime.now(timezone.utc)
        emp_skill = EmployeeSkill(
            id=self._next_skill_id,
            employee_id=employee_id,
            skill_id=skill_id,
            skill_name="",
            proficiency=proficiency,
            created_at=now,
            updated_at=now,
        )
        self._skills[self._next_skill_id] = emp_skill
        self._next_skill_id += 1
        return emp_skill

    async def update_skill_proficiency(
        self, employee_skill_id: int, proficiency: ProficiencyLevel
    ) -> None:
        if employee_skill_id in self._skills:
            self._skills[employee_skill_id].proficiency = proficiency

    async def remove_skill(self, employee_skill_id: int) -> None:
        self._skills.pop(employee_skill_id, None)

    async def find_by_manager(self, manager_user_id: int) -> list[Employee]:
        return [
            e for e in self._store.values()
            if e.manager_user_id == manager_user_id and e.is_active
        ]


class InMemorySkillRepository(ISkillRepository):
    """Fake skill repository for unit tests."""

    def __init__(self) -> None:
        self._store: dict[int, Skill] = {}
        self._by_name: dict[str, int] = {}
        self._next_id = 1

    async def find_by_id(self, skill_id: int) -> Skill | None:
        return self._store.get(skill_id)

    async def find_all(self) -> list[Skill]:
        return sorted(self._store.values(), key=lambda s: s.name)

    async def find_by_name(self, name: str) -> Skill | None:
        sid = self._by_name.get(name)
        return self._store.get(sid) if sid else None

    async def save(self, skill: Skill) -> Skill:
        if skill.id is None:
            skill.id = self._next_id
            self._next_id += 1
        self._store[skill.id] = skill
        self._by_name[skill.name] = skill.id
        return skill


# ── helpers ───────────────────────────────────────────────────────────────────


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


def make_skill(
    skill_id: int = 1,
    name: str = "Python",
    category: str = "Technical",
) -> Skill:
    now = datetime.now(timezone.utc)
    return Skill(id=skill_id, name=name, category=category, created_at=now, updated_at=now)


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def fake_employee_repo() -> InMemoryEmployeeRepository:
    return InMemoryEmployeeRepository()


@pytest.fixture
def fake_skill_repo() -> InMemorySkillRepository:
    return InMemorySkillRepository()


# ── InMemoryProjectRepository ─────────────────────────────────────────────────


class InMemoryProjectRepository(IProjectRepository):

    def __init__(self) -> None:
        self._store: dict[int, Project] = {}
        self._next_id = 1

    async def find_by_id(self, project_id: int) -> Project | None:
        return self._store.get(project_id)

    async def find_all(
        self,
        status: ProjectStatus | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Project], int]:
        items = list(self._store.values())
        if status is not None:
            items = [p for p in items if p.status == status]
        if manager_user_id is not None:
            items = [p for p in items if p.manager_user_id == manager_user_id]
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    async def find_by_name(self, name: str) -> Project | None:
        for p in self._store.values():
            if p.name == name:
                return p
        return None

    async def save(self, project: Project) -> Project:
        if project.id is None:
            project.id = self._next_id
            self._next_id += 1
        else:
            self._next_id = max(self._next_id, project.id + 1)
        self._store[project.id] = project
        return project

    async def update_status(self, project_id: int, status: ProjectStatus) -> None:
        if project_id in self._store:
            self._store[project_id].status = status

    async def update_completed_points(self, project_id: int, points: int) -> None:
        if project_id in self._store:
            self._store[project_id].completed_story_points = points


# ── InMemoryMilestoneRepository ───────────────────────────────────────────────


class InMemoryMilestoneRepository(IMilestoneRepository):

    def __init__(self) -> None:
        self._store: dict[int, Milestone] = {}
        self._next_id = 1

    async def find_by_id(self, milestone_id: int) -> Milestone | None:
        return self._store.get(milestone_id)

    async def find_by_project(self, project_id: int) -> list[Milestone]:
        return [m for m in self._store.values() if m.project_id == project_id]

    async def save(self, milestone: Milestone) -> Milestone:
        if milestone.id is None:
            milestone.id = self._next_id
            self._next_id += 1
        else:
            self._next_id = max(self._next_id, milestone.id + 1)
        self._store[milestone.id] = milestone
        return milestone

    async def update_status(self, milestone_id: int, status: MilestoneStatus) -> None:
        if milestone_id in self._store:
            self._store[milestone_id].status = status

    async def sum_done_story_points(self, project_id: int) -> int:
        return sum(
            m.story_points
            for m in self._store.values()
            if m.project_id == project_id and m.status == MilestoneStatus.DONE
        )


# ── Factory helpers ───────────────────────────────────────────────────────────


def make_project(
    project_id: int = 1,
    name: str = "Alpha Project",
    manager_user_id: int = 2,
    status: ProjectStatus = ProjectStatus.PLANNED,
    total_story_points: int = 100,
    completed_story_points: int = 0,
) -> Project:
    now = datetime.now(timezone.utc)
    return Project(
        id=project_id,
        name=name,
        description=None,
        manager_user_id=manager_user_id,
        status=status,
        total_story_points=total_story_points,
        completed_story_points=completed_story_points,
        start_date=None,
        end_date=None,
        created_at=now,
        updated_at=now,
    )


def make_milestone(
    milestone_id: int = 1,
    project_id: int = 1,
    title: str = "M1",
    status: MilestoneStatus = MilestoneStatus.PENDING,
    story_points: int = 10,
) -> Milestone:
    now = datetime.now(timezone.utc)
    return Milestone(
        id=milestone_id,
        project_id=project_id,
        title=title,
        description=None,
        due_date=None,
        status=status,
        story_points=story_points,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def fake_project_repo() -> InMemoryProjectRepository:
    return InMemoryProjectRepository()


@pytest.fixture
def fake_milestone_repo() -> InMemoryMilestoneRepository:
    return InMemoryMilestoneRepository()


# ── InMemoryAllocationRepository ──────────────────────────────────────────────


class InMemoryAllocationRepository(IAllocationRepository):

    def __init__(self) -> None:
        self._store: dict[int, Allocation] = {}
        self._next_id = 1

    async def find_by_id(self, allocation_id: int) -> Allocation | None:
        return self._store.get(allocation_id)

    async def find_active_by_employee(self, employee_id: int) -> list[Allocation]:
        return [
            a for a in self._store.values()
            if a.employee_id == employee_id and a.status == AllocationStatus.ACTIVE
        ]

    async def find_by_project(
        self,
        project_id: int,
        active_only: bool = False,
    ) -> list[Allocation]:
        result = [a for a in self._store.values() if a.project_id == project_id]
        if active_only:
            result = [a for a in result if a.status == AllocationStatus.ACTIVE]
        return result

    async def find_by_employee(
        self,
        employee_id: int,
        active_only: bool = False,
    ) -> list[Allocation]:
        result = [a for a in self._store.values() if a.employee_id == employee_id]
        if active_only:
            result = [a for a in result if a.status == AllocationStatus.ACTIVE]
        return result

    async def save(self, allocation: Allocation) -> Allocation:
        if allocation.id is None:
            allocation.id = self._next_id
            self._next_id += 1
        else:
            self._next_id = max(self._next_id, allocation.id + 1)
        self._store[allocation.id] = allocation
        return allocation

    async def end_allocation(self, allocation_id: int, ended_at) -> None:
        if allocation_id in self._store:
            a = self._store[allocation_id]
            a.status = AllocationStatus.ENDED
            a.to_date = ended_at
            a.updated_at = datetime.now(timezone.utc)


# ── Factory helpers ───────────────────────────────────────────────────────────


def make_allocation(
    allocation_id: int = 1,
    employee_id: int = 10,
    project_id: int = 1,
    utilization_percent: int = 50,
    status: AllocationStatus = AllocationStatus.ACTIVE,
) -> Allocation:
    from datetime import date
    now = datetime.now(timezone.utc)
    return Allocation(
        id=allocation_id,
        employee_id=employee_id,
        project_id=project_id,
        utilization_percent=utilization_percent,
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
        status=status,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def fake_allocation_repo() -> InMemoryAllocationRepository:
    return InMemoryAllocationRepository()


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
