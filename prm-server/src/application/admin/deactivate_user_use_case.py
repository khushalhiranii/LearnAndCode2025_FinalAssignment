from src.application.dtos.user_dtos import UserResponse
from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.exceptions import AuthorizationError, CannotDeactivateSelfError, UserNotFoundError
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository


class DeactivateUserUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._users = user_repo
        self._employees = employee_repo

    async def execute(
        self,
        target_user_id: int,
        acting_admin_id: int,
    ) -> UserResponse:
        if target_user_id == acting_admin_id:
            raise CannotDeactivateSelfError("Admins cannot deactivate themselves.")

        user = await self._users.find_by_id(target_user_id)
        if user is None:
            raise UserNotFoundError(f"User {target_user_id} not found.")

        await self._users.update_active(target_user_id, is_active=False)

        # Cascade to employee profile if it exists
        employee = await self._employees.find_by_user_id(target_user_id)
        if employee is not None:
            await self._employees.update_active(employee.id, is_active=False)  # type: ignore[arg-type]

        return UserResponse(
            id=user.id,  # type: ignore[arg-type]
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=False,
            force_password_change=user.force_password_change,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
