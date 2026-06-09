import secrets
import string
from datetime import datetime, timezone

from src.application.dtos.user_dtos import CreateUserRequest, UserResponse
from src.domain.entities.employee import Employee
from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.exceptions import DuplicateEmailError, DuplicateUsernameError
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository
from src.infrastructure.security.password_hasher import hash_password

_TEMP_PWD_ALPHABET = string.ascii_letters + string.digits + "!@#$%"
_TEMP_PWD_LENGTH = 12


def _generate_temp_password() -> str:
    return "".join(secrets.choice(_TEMP_PWD_ALPHABET) for _ in range(_TEMP_PWD_LENGTH))


class CreateUserUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._users = user_repo
        self._employees = employee_repo

    async def execute(self, request: CreateUserRequest) -> tuple[UserResponse, str]:
        """Returns (UserResponse, temp_password)."""
        # Check uniqueness
        if await self._users.find_by_username(request.username) is not None:
            raise DuplicateUsernameError(f"Username '{request.username}' already exists.")
        if await self._users.find_by_email(request.email) is not None:
            raise DuplicateEmailError(f"Email '{request.email}' already registered.")

        temp_password = _generate_temp_password()
        now = datetime.now(timezone.utc)
        user = User(
            id=None,
            full_name=request.full_name,
            email=request.email,
            username=request.username,
            password_hash=hash_password(temp_password),
            role=request.role,
            is_active=True,
            force_password_change=True,
            created_at=now,
            updated_at=now,
        )
        saved_user = await self._users.save(user)

        # Auto-create employee profile for MANAGER and EMPLOYEE roles
        if request.role in (Role.MANAGER, Role.EMPLOYEE):
            employee = Employee(
                id=None,
                user_id=saved_user.id,  # type: ignore[arg-type]
                full_name=saved_user.full_name,
                email=saved_user.email,
                department=None,
                designation=None,
                date_of_joining=None,
                manager_user_id=None,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            await self._employees.save(employee)

        return _user_to_response(saved_user), temp_password


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,  # type: ignore[arg-type]
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        force_password_change=user.force_password_change,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
