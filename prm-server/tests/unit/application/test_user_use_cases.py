"""Unit tests for admin user management use cases."""

from datetime import datetime, timezone

import pytest

from src.application.admin.create_user_use_case import CreateUserUseCase
from src.application.admin.deactivate_user_use_case import DeactivateUserUseCase
from src.application.admin.list_users_use_case import ListUsersUseCase
from src.application.admin.reactivate_user_use_case import ReactivateUserUseCase
from src.application.admin.reset_password_use_case import ResetPasswordUseCase
from src.application.dtos.user_dtos import CreateUserRequest
from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.exceptions import (
    CannotDeactivateSelfError,
    DuplicateEmailError,
    DuplicateUsernameError,
    UserNotFoundError,
)
from src.infrastructure.security.password_hasher import verify_password
from tests.conftest import InMemoryEmployeeRepository, InMemoryUserRepository, make_admin_user


# ── CreateUserUseCase ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_returns_response_and_temp_password():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = CreateUserUseCase(user_repo, emp_repo)

    response, temp_pwd = await use_case.execute(
        CreateUserRequest(
            username="jdoe",
            email="jdoe@example.com",
            full_name="Jane Doe",
            role=Role.EMPLOYEE,
        )
    )

    assert response.username == "jdoe"
    assert response.role == Role.EMPLOYEE
    assert response.force_password_change is True
    assert len(temp_pwd) == 12


@pytest.mark.asyncio
async def test_create_user_auto_creates_employee_profile_for_employee_role():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = CreateUserUseCase(user_repo, emp_repo)

    response, _ = await use_case.execute(
        CreateUserRequest(
            username="jdoe",
            email="jdoe@example.com",
            full_name="Jane Doe",
            role=Role.EMPLOYEE,
        )
    )

    employee = await emp_repo.find_by_user_id(response.id)
    assert employee is not None
    assert employee.user_id == response.id


@pytest.mark.asyncio
async def test_create_user_auto_creates_employee_profile_for_manager_role():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = CreateUserUseCase(user_repo, emp_repo)

    response, _ = await use_case.execute(
        CreateUserRequest(
            username="mgr1",
            email="mgr1@example.com",
            full_name="Manager One",
            role=Role.MANAGER,
        )
    )

    employee = await emp_repo.find_by_user_id(response.id)
    assert employee is not None


@pytest.mark.asyncio
async def test_create_user_no_employee_profile_for_admin_role():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = CreateUserUseCase(user_repo, emp_repo)

    response, _ = await use_case.execute(
        CreateUserRequest(
            username="admin2",
            email="admin2@example.com",
            full_name="Admin Two",
            role=Role.ADMIN,
        )
    )

    employee = await emp_repo.find_by_user_id(response.id)
    assert employee is None


@pytest.mark.asyncio
async def test_create_user_raises_on_duplicate_username():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = CreateUserUseCase(user_repo, emp_repo)

    await use_case.execute(
        CreateUserRequest(
            username="jdoe",
            email="jdoe@example.com",
            full_name="Jane Doe",
            role=Role.EMPLOYEE,
        )
    )

    with pytest.raises(DuplicateUsernameError):
        await use_case.execute(
            CreateUserRequest(
                username="jdoe",
                email="other@example.com",
                full_name="Another",
                role=Role.EMPLOYEE,
            )
        )


@pytest.mark.asyncio
async def test_create_user_raises_on_duplicate_email():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = CreateUserUseCase(user_repo, emp_repo)

    await use_case.execute(
        CreateUserRequest(
            username="jdoe",
            email="jdoe@example.com",
            full_name="Jane Doe",
            role=Role.EMPLOYEE,
        )
    )

    with pytest.raises(DuplicateEmailError):
        await use_case.execute(
            CreateUserRequest(
                username="other",
                email="jdoe@example.com",
                full_name="Another",
                role=Role.EMPLOYEE,
            )
        )


# ── DeactivateUserUseCase ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_user_sets_inactive():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    admin = make_admin_user()
    await user_repo.save(admin)

    target = User(
        id=None,
        full_name="Target User",
        email="target@example.com",
        username="target",
        password_hash="x",
        is_account_enabled=True,
        force_password_change=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    saved_target = await user_repo.save(target)

    use_case = DeactivateUserUseCase(user_repo, emp_repo)
    result = await use_case.execute(saved_target.id, acting_admin_id=admin.id)

    assert result.is_account_enabled is False
    stored = await user_repo.find_by_id(saved_target.id)
    assert stored.is_account_enabled is False


@pytest.mark.asyncio
async def test_deactivate_self_raises_cannot_deactivate_self():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    admin = make_admin_user()
    await user_repo.save(admin)

    use_case = DeactivateUserUseCase(user_repo, emp_repo)

    with pytest.raises(CannotDeactivateSelfError):
        await use_case.execute(admin.id, acting_admin_id=admin.id)


@pytest.mark.asyncio
async def test_deactivate_nonexistent_user_raises_user_not_found():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    use_case = DeactivateUserUseCase(user_repo, emp_repo)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(999, acting_admin_id=1)


# ── ReactivateUserUseCase ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reactivate_user_sets_active():
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()

    user = User(
        id=None,
        full_name="Deactivated User",
        email="d@example.com",
        username="duser",
        password_hash="x",
        is_account_enabled=False,
        force_password_change=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    saved = await user_repo.save(user)

    use_case = ReactivateUserUseCase(user_repo, emp_repo)
    result = await use_case.execute(saved.id)

    assert result.is_account_enabled is True


# ── ResetPasswordUseCase ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_password_sets_force_change_flag():
    user_repo = InMemoryUserRepository()
    admin = make_admin_user(force_password_change=False)
    await user_repo.save(admin)

    use_case = ResetPasswordUseCase(user_repo)
    result = await use_case.execute(admin.id)

    assert len(result.temp_password) == 12
    stored = await user_repo.find_by_id(admin.id)
    assert stored.force_password_change is True
    assert verify_password(result.temp_password, stored.password_hash)


@pytest.mark.asyncio
async def test_reset_password_raises_for_unknown_user():
    user_repo = InMemoryUserRepository()
    use_case = ResetPasswordUseCase(user_repo)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(999)


# ── ListUsersUseCase ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_returns_all():
    user_repo = InMemoryUserRepository()
    for i in range(3):
        saved = await user_repo.save(
            User(
                id=None,
                full_name=f"User {i}",
                email=f"u{i}@example.com",
                username=f"u{i}",
                password_hash="x",
                is_account_enabled=True,
                force_password_change=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await user_repo.assign_role(saved.id, Role.EMPLOYEE, __import__("datetime").date.today(), None, None)

    use_case = ListUsersUseCase(user_repo)
    result = await use_case.execute()

    assert result.total == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_list_users_filters_by_role():
    user_repo = InMemoryUserRepository()
    admin_saved = await user_repo.save(
        User(
            id=None,
            full_name="Admin",
            email="admin@x.com",
            username="admin",
            password_hash="x",
            is_account_enabled=True,
            force_password_change=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    await user_repo.assign_role(admin_saved.id, Role.ADMIN, __import__("datetime").date.today(), None, None)
    emp_saved = await user_repo.save(
        User(
            id=None,
            full_name="Employee",
            email="emp@x.com",
            username="emp",
            password_hash="x",
            is_account_enabled=True,
            force_password_change=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    await user_repo.assign_role(emp_saved.id, Role.EMPLOYEE, __import__("datetime").date.today(), None, None)

    use_case = ListUsersUseCase(user_repo)
    result = await use_case.execute(role=Role.EMPLOYEE)

    assert result.total == 1
    assert result.items[0].role == Role.EMPLOYEE
