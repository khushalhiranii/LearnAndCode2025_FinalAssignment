"""Unit tests for admin employee management use cases."""

from datetime import datetime, timezone

import pytest

from src.application.admin.assign_manager_use_case import AssignManagerUseCase
from src.application.admin.deactivate_employee_use_case import DeactivateEmployeeUseCase
from src.application.admin.list_employees_use_case import ListEmployeesUseCase
from src.application.admin.skill_use_case import SkillUseCase
from src.application.admin.update_employee_use_case import UpdateEmployeeUseCase
from src.application.dtos.employee_dtos import (
    AddSkillRequest,
    CreateSkillRequest,
    UpdateEmployeeRequest,
    UpdateSkillRequest,
)
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.entities.user import User
from src.domain.enums import AllocationStatus, ProficiencyLevel, Role
from src.domain.exceptions import (
    CannotDeactivateSelfError,
    DuplicateSkillError,
    EmployeeNotFoundError,
    InvalidManagerError,
    SkillNotFoundError,
)
from tests.conftest import (
    InMemoryAllocationRepository,
    InMemoryEmployeeRepository,
    InMemorySkillRepository,
    InMemoryUserRepository,
    make_admin_user,
    make_allocation,
    make_skill,
)


def _make_employee(
    user_id: int = 2,
    emp_id: int | None = None,
    is_available: bool = True,
) -> ResourceProfile:
    now = datetime.now(timezone.utc)
    return ResourceProfile(
        id=emp_id,
        user_id=user_id,
        full_name="Test Employee",
        email="emp@example.com",
        department=None,
        designation=None,
        date_of_joining=None,
        manager_user_id=None,
        is_available=is_available,
        created_at=now,
        updated_at=now,
    )


def _make_user(
    user_id: int,
    username: str = "emp1",
    email: str = "emp1@example.com",
    is_account_enabled: bool = True,
) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=user_id,
        full_name="Test User",
        email=email,
        username=username,
        password_hash="x",
        is_account_enabled=is_account_enabled,
        force_password_change=False,
        created_at=now,
        updated_at=now,
    )


# ── UpdateEmployeeUseCase ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_employee_updates_department():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()

    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)
    await user_repo.save(_make_user(2))

    use_case = UpdateEmployeeUseCase(user_repo, emp_repo)
    result = await use_case.execute(
        employee.id, UpdateEmployeeRequest(department="Engineering")
    )

    assert result.department == "Engineering"


@pytest.mark.asyncio
async def test_update_employee_raises_for_unknown():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()

    use_case = UpdateEmployeeUseCase(user_repo, emp_repo)

    with pytest.raises(EmployeeNotFoundError):
        await use_case.execute(999, UpdateEmployeeRequest())


# ── DeactivateEmployeeUseCase ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_employee_sets_inactive():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()
    alloc_repo = InMemoryAllocationRepository()

    admin = make_admin_user()
    await user_repo.save(admin)
    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)
    target_user = _make_user(2)
    await user_repo.save(target_user)

    use_case = DeactivateEmployeeUseCase(user_repo, emp_repo, alloc_repo)
    result = await use_case.execute(employee.id, acting_admin_id=admin.id)

    assert result.is_available is False
    stored = await emp_repo.find_by_id(employee.id)
    assert stored.is_available is False


@pytest.mark.asyncio
async def test_deactivate_employee_self_raises():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()
    alloc_repo = InMemoryAllocationRepository()

    employee = _make_employee(user_id=1)
    await emp_repo.save(employee)

    use_case = DeactivateEmployeeUseCase(user_repo, emp_repo, alloc_repo)

    with pytest.raises(CannotDeactivateSelfError):
        await use_case.execute(employee.id, acting_admin_id=1)


@pytest.mark.asyncio
async def test_deactivate_employee_ends_active_allocations():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()
    alloc_repo = InMemoryAllocationRepository()

    admin = make_admin_user()
    await user_repo.save(admin)
    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)
    target_user = _make_user(2)
    await user_repo.save(target_user)

    alloc1 = make_allocation(allocation_id=1, resource_profile_id=employee.id, project_id=1)
    alloc2 = make_allocation(allocation_id=2, resource_profile_id=employee.id, project_id=2)
    await alloc_repo.save(alloc1)
    await alloc_repo.save(alloc2)

    use_case = DeactivateEmployeeUseCase(user_repo, emp_repo, alloc_repo)
    await use_case.execute(employee.id, acting_admin_id=admin.id)

    ended1 = await alloc_repo.find_by_id(alloc1.id)
    ended2 = await alloc_repo.find_by_id(alloc2.id)
    assert ended1.status == AllocationStatus.ENDED
    assert ended2.status == AllocationStatus.ENDED


# ── AssignManagerUseCase ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_assign_manager_sets_manager():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()

    manager_user = _make_user(10, username="mgr", email="mgr@x.com")
    await user_repo.save(manager_user)
    await user_repo.assign_role(10, Role.MANAGER, __import__("datetime").date.today(), None, None)

    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)
    await user_repo.save(_make_user(2))

    use_case = AssignManagerUseCase(user_repo, emp_repo)
    result = await use_case.execute(employee.id, manager_user_id=10)

    assert result.manager_user_id == 10


@pytest.mark.asyncio
async def test_assign_self_as_manager_raises():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()

    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)

    use_case = AssignManagerUseCase(user_repo, emp_repo)

    with pytest.raises(InvalidManagerError):
        await use_case.execute(employee.id, manager_user_id=employee.user_id)


@pytest.mark.asyncio
async def test_assign_non_manager_role_raises():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()

    wrong_role_user = _make_user(10, username="emp2", email="emp2@x.com")
    await user_repo.save(wrong_role_user)
    await user_repo.assign_role(10, Role.EMPLOYEE, __import__("datetime").date.today(), None, None)

    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)
    await user_repo.save(_make_user(2))

    use_case = AssignManagerUseCase(user_repo, emp_repo)

    with pytest.raises(InvalidManagerError):
        await use_case.execute(employee.id, manager_user_id=10)


# ── SkillUseCase ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_skill_returns_response():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()

    use_case = SkillUseCase(skill_repo, emp_repo)
    result = await use_case.create_skill(
        CreateSkillRequest(name="Python", category="Technical")
    )

    assert result.name == "Python"
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_duplicate_skill_raises():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = SkillUseCase(skill_repo, emp_repo)

    await use_case.create_skill(CreateSkillRequest(name="Python", category="Technical"))

    with pytest.raises(DuplicateSkillError):
        await use_case.create_skill(CreateSkillRequest(name="Python", category="Technical"))


@pytest.mark.asyncio
async def test_add_skill_to_employee():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()

    skill = make_skill()
    await skill_repo.save(skill)
    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)

    use_case = SkillUseCase(skill_repo, emp_repo)
    result = await use_case.add_skill_to_employee(
        employee.id, AddSkillRequest(skill_id=skill.id, proficiency=ProficiencyLevel.BEGINNER)
    )

    assert result.skill_id == skill.id
    assert result.proficiency == ProficiencyLevel.BEGINNER


@pytest.mark.asyncio
async def test_add_duplicate_skill_raises():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()

    skill = make_skill()
    await skill_repo.save(skill)
    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)

    use_case = SkillUseCase(skill_repo, emp_repo)
    await use_case.add_skill_to_employee(
        employee.id, AddSkillRequest(skill_id=skill.id, proficiency=ProficiencyLevel.BEGINNER)
    )

    with pytest.raises(DuplicateSkillError):
        await use_case.add_skill_to_employee(
            employee.id,
            AddSkillRequest(skill_id=skill.id, proficiency=ProficiencyLevel.ADVANCED),
        )


@pytest.mark.asyncio
async def test_update_skill_proficiency():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()

    skill = make_skill()
    await skill_repo.save(skill)
    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)

    use_case = SkillUseCase(skill_repo, emp_repo)
    await use_case.add_skill_to_employee(
        employee.id, AddSkillRequest(skill_id=skill.id, proficiency=ProficiencyLevel.BEGINNER)
    )

    result = await use_case.update_employee_skill(
        employee.id, skill.id, UpdateSkillRequest(proficiency=ProficiencyLevel.ADVANCED)
    )

    assert result.proficiency == ProficiencyLevel.ADVANCED


@pytest.mark.asyncio
async def test_remove_skill():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()

    skill = make_skill()
    await skill_repo.save(skill)
    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)

    use_case = SkillUseCase(skill_repo, emp_repo)
    await use_case.add_skill_to_employee(
        employee.id, AddSkillRequest(skill_id=skill.id, proficiency=ProficiencyLevel.BEGINNER)
    )
    await use_case.remove_employee_skill(employee.id, skill.id)

    skills = await use_case.list_employee_skills(employee.id)
    assert len(skills) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_skill_raises():
    skill_repo = InMemorySkillRepository()
    emp_repo = InMemoryEmployeeRepository()

    employee = _make_employee(user_id=2)
    await emp_repo.save(employee)

    use_case = SkillUseCase(skill_repo, emp_repo)

    with pytest.raises(SkillNotFoundError):
        await use_case.remove_employee_skill(employee.id, 999)


# ── ListEmployeesUseCase ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_employees_returns_all():
    emp_repo = InMemoryEmployeeRepository()
    user_repo = InMemoryUserRepository()

    for i in range(3):
        user = _make_user(i + 2, username=f"u{i}", email=f"u{i}@x.com")
        await user_repo.save(user)
        await emp_repo.save(_make_employee(user_id=i + 2))

    use_case = ListEmployeesUseCase(user_repo, emp_repo, InMemoryAllocationRepository())
    result = await use_case.execute()

    assert result.total == 3
    assert len(result.items) == 3
