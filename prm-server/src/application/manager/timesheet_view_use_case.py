from datetime import date, timedelta

from src.application.dtos.timesheet_dtos import (
    ManagerTimesheetListResponse,
    ManagerTimesheetRow,
    TimesheetResponse,
)
from src.application.employee.timesheet_use_case import _to_response
from src.domain.enums import TimesheetStatus
from src.domain.exceptions import AuthorizationError, EmployeeNotFoundError
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    IProjectRepository,
    ITimesheetRepository,
)


class TimesheetViewUseCase:

    def __init__(
        self,
        timesheet_repo: ITimesheetRepository,
        employee_repo: IEmployeeRepository,
        project_repo: IProjectRepository,
        allocation_repo: IAllocationRepository,
    ) -> None:
        self._timesheets = timesheet_repo
        self._employees = employee_repo
        self._projects = project_repo
        self._allocations = allocation_repo

    async def list_team_timesheets(
        self, manager_user_id: int, week_start: date | None = None
    ) -> ManagerTimesheetListResponse:
        if not week_start:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        employees = await self._employees.find_by_manager(manager_user_id)
        rows: list[ManagerTimesheetRow] = []

        for emp in employees:
            timesheet = await self._timesheets.find_by_employee_and_week(
                emp.id, week_start
            )
            week_allocs = await self._allocations.find_active_by_employee_and_week(
                emp.id, week_start
            )

            if timesheet and timesheet.status == TimesheetStatus.SUBMITTED:
                full_ts = await self._timesheets.find_by_id(timesheet.id)  # type: ignore[arg-type]
                for entry in full_ts.entries:
                    project = await self._projects.find_by_id(entry.project_id)
                    pname = project.name if project else "Unknown"
                    rows.append(
                        ManagerTimesheetRow(
                            resource_profile_id=emp.id,
                            timesheet_id=full_ts.id,
                            employee_name=emp.full_name,
                            project_name=pname,
                            hours=entry.hours_worked,
                            status=timesheet.status,
                        )
                    )
            elif week_allocs:
                for alloc in week_allocs:
                    project = await self._projects.find_by_id(alloc.project_id)
                    pname = project.name if project else "Unknown"
                    rows.append(
                        ManagerTimesheetRow(
                            resource_profile_id=emp.id,
                            timesheet_id=None,
                            employee_name=emp.full_name,
                            project_name=pname,
                            hours=0.0,
                            status=TimesheetStatus.MISSED,
                        )
                    )

        return ManagerTimesheetListResponse(week_start_date=week_start, items=rows)

    async def get_team_timesheet_detail(
        self,
        manager_user_id: int,
        resource_profile_id: int,
        week_start: date,
    ) -> TimesheetResponse:
        employee = await self._employees.find_by_id(resource_profile_id)
        if employee is None:
            raise EmployeeNotFoundError(
                f"Employee {resource_profile_id} not found."
            )
        if employee.manager_user_id != manager_user_id:
            raise AuthorizationError(
                "You can only view timesheets for employees on your team."
            )

        timesheet = await self._timesheets.find_by_employee_and_week(
            resource_profile_id, week_start
        )
        if timesheet is None or timesheet.status != TimesheetStatus.SUBMITTED:
            raise EmployeeNotFoundError(
                f"No submitted timesheet for employee {resource_profile_id} "
                f"in week starting {week_start}."
            )

        full_ts = await self._timesheets.find_by_id(timesheet.id)  # type: ignore[arg-type]
        return _to_response(full_ts)
