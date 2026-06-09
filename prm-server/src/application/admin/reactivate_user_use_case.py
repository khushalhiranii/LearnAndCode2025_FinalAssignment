from src.application.dtos.user_dtos import UserResponse
from src.domain.exceptions import UserNotFoundError
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository


class ReactivateUserUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._users = user_repo
        self._employees = employee_repo

    async def execute(self, target_user_id: int) -> UserResponse:
        user = await self._users.find_by_id(target_user_id)
        if user is None:
            raise UserNotFoundError(f"User {target_user_id} not found.")

        await self._users.update_active(target_user_id, is_active=True)

        employee = await self._employees.find_by_user_id(target_user_id)
        if employee is not None:
            await self._employees.update_active(employee.id, is_active=True)  # type: ignore[arg-type]

        return UserResponse(
            id=user.id,  # type: ignore[arg-type]
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=True,
            force_password_change=user.force_password_change,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
