from src.application.dtos.employee_dtos import EmployeeResponse
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.enums import Role
from src.domain.exceptions import EmployeeNotFoundError, InvalidManagerError, UserNotFoundError
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository


class AssignManagerUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._users = user_repo
        self._employees = employee_repo

    async def execute(
        self,
        employee_id: int,
        manager_user_id: int | None,
    ) -> EmployeeResponse:
        employee = await self._employees.find_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")

        if manager_user_id is not None:
            if manager_user_id == employee.user_id:
                raise InvalidManagerError("An employee cannot be their own manager.")

            manager = await self._users.find_by_id(manager_user_id)
            if manager is None:
                raise UserNotFoundError(f"Manager user {manager_user_id} not found.")
            manager_role = await self._users.find_active_role(manager_user_id)
            if manager_role != Role.MANAGER:
                raise InvalidManagerError("The designated manager must have MANAGER role.")
            if not manager.is_account_enabled:
                raise InvalidManagerError("The designated manager is inactive.")

        await self._employees.update_manager(employee_id, manager_user_id)

        user = await self._users.find_by_id(employee.user_id)
        employee.manager_user_id = manager_user_id
        return _to_response(employee, user.full_name if user else "", user.email if user else "")


def _to_response(employee: ResourceProfile, full_name: str, email: str) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,  # type: ignore[arg-type]
        user_id=employee.user_id,
        full_name=full_name,
        email=email,
        department=employee.department,
        designation=employee.designation,
        date_of_joining=employee.date_of_joining,
        manager_user_id=employee.manager_user_id,
        is_available=employee.is_available,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )
