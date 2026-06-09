from src.application.dtos.employee_dtos import EmployeeListResponse, EmployeeResponse
from src.domain.entities.employee import Employee
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository


class ListEmployeesUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._users = user_repo
        self._employees = employee_repo

    async def execute(
        self,
        is_active: bool | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> EmployeeListResponse:
        employees, total = await self._employees.find_all(
            is_active=is_active,
            manager_user_id=manager_user_id,
            page=page,
            page_size=page_size,
        )

        items: list[EmployeeResponse] = []
        for emp in employees:
            user = await self._users.find_by_id(emp.user_id)
            items.append(
                EmployeeResponse(
                    id=emp.id,  # type: ignore[arg-type]
                    user_id=emp.user_id,
                    full_name=user.full_name if user else "",
                    email=user.email if user else "",
                    department=emp.department,
                    designation=emp.designation,
                    date_of_joining=emp.date_of_joining,
                    manager_user_id=emp.manager_user_id,
                    is_active=emp.is_active,
                    created_at=emp.created_at,
                    updated_at=emp.updated_at,
                )
            )

        return EmployeeListResponse(items=items, total=total, page=page, page_size=page_size)
