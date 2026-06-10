from datetime import date

from src.application.dtos.employee_dtos import EmployeeResponse
from src.domain.entities.employee import Employee
from src.domain.exceptions import CannotDeactivateSelfError, EmployeeNotFoundError
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    IUserRepository,
)


class DeactivateEmployeeUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        employee_repo: IEmployeeRepository,
        allocation_repo: IAllocationRepository,
    ) -> None:
        self._users = user_repo
        self._employees = employee_repo
        self._allocations = allocation_repo

    async def execute(self, employee_id: int, acting_admin_id: int) -> EmployeeResponse:
        employee = await self._employees.find_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")

        if employee.user_id == acting_admin_id:
            raise CannotDeactivateSelfError("Cannot deactivate yourself.")

        # End all active allocations immediately (BRD Screen 3.1.2 + Sequence Diagram 6.4)
        active_allocations = await self._allocations.find_active_by_employee(employee_id)
        today = date.today()
        for allocation in active_allocations:
            await self._allocations.end_allocation(allocation.id, today)

        await self._employees.update_active(employee_id, is_active=False)
        await self._users.update_active(employee.user_id, is_active=False)

        user = await self._users.find_by_id(employee.user_id)
        return _to_response(employee, user.full_name if user else "", user.email if user else "")


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
        is_active=False,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )
