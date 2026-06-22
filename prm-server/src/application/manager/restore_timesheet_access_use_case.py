from datetime import datetime, timezone

from src.application.notifications.email_notification_service import EmailNotificationService
from src.domain.enums import NotificationType
from src.domain.exceptions import AuthorizationError, EmployeeNotFoundError
from src.domain.ports.repositories import IEmployeeRepository, IUserRepository
from src.infrastructure.email.templates import timesheet_restored_html


class RestoreTimesheetAccessUseCase:

    def __init__(
        self,
        employees: IEmployeeRepository,
        users: IUserRepository,
        email_service: EmailNotificationService,
    ) -> None:
        self._employees = employees
        self._users = users
        self._email = email_service

    async def execute(self, manager_user_id: int, employee_id: int) -> dict[str, str]:
        employee = await self._employees.find_by_id(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        if employee.manager_user_id != manager_user_id:
            raise AuthorizationError("You can only restore access for your own team members.")

        await self._employees.update_timesheet_freeze(
            employee_id, False, None, None
        )

        user = await self._users.find_by_id(employee.user_id)
        if user and user.email:
            await self._email.send_if_new(
                NotificationType.TIMESHEET_ACCESS_RESTORED,
                user.id,  # type: ignore[arg-type]
                user.email,
                employee_id,
                datetime.now(timezone.utc).date().isoformat(),
                "Timesheet submission access restored",
                timesheet_restored_html(user.full_name),
            )

        return {"message": "Timesheet submission access restored.", "employee_id": employee_id}
