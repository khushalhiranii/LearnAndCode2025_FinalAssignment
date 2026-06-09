from datetime import date

from src.application.dtos.employee_dtos import EmployeeResponse, UpdateEmployeeRequest
from src.domain.entities.employee import Employee
from src.domain.exceptions import EmployeeNotFoundError
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository


class UpdateEmployeeUseCase:

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
        request: UpdateEmployeeRequest,
    ) -> EmployeeResponse:
        employee = await self._employees.find_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")

        # Apply partial updates (None = not provided = keep existing)
        if request.department is not None:
            employee.department = request.department
        if request.designation is not None:
            employee.designation = request.designation
        if request.date_of_joining is not None:
            employee.date_of_joining = request.date_of_joining

        updated = await self._employees.save(employee)
        user = await self._users.find_by_id(updated.user_id)

        return _to_response(updated, user.full_name if user else "", user.email if user else "")


def _to_response(employee: Employee, full_name: str, email: str) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,  # type: ignore[arg-type]
        user_id=employee.user_id,
        full_name=full_name,
        email=email,
        department=employee.department,
        designation=employee.designation,
        date_of_joining=employee.date_of_joining,
        manager_user_id=employee.manager_user_id,
        is_active=employee.is_active,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )
