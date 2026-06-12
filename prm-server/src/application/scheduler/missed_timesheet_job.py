import json
from datetime import date, datetime, timedelta, timezone

from src.domain.entities.timesheet import Timesheet
from src.domain.enums import TimesheetStatus
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    ITimesheetRepository,
)


def _prior_monday(reference: date | None = None) -> date:
    today = reference or date.today()
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    return this_monday - timedelta(days=7)


class MissedTimesheetJob:

    def __init__(
        self,
        employees: IEmployeeRepository,
        allocations: IAllocationRepository,
        timesheets: ITimesheetRepository,
    ) -> None:
        self._employees = employees
        self._allocations = allocations
        self._timesheets = timesheets

    async def run(self) -> int:
        week_start = _prior_monday()
        flagged = 0
        employees, _ = await self._employees.find_all(is_active=True, page=1, page_size=10000)
        for emp in employees:
            if emp.id is None:
                continue
            week_allocs = await self._allocations.find_active_by_employee_and_week(
                emp.id, week_start
            )
            if not week_allocs:
                continue
            existing = await self._timesheets.find_by_employee_and_week(emp.id, week_start)
            if existing and existing.status == TimesheetStatus.SUBMITTED:
                continue
            if existing and existing.status == TimesheetStatus.MISSED:
                continue
            missed = Timesheet(
                id=None,
                resource_profile_id=emp.id,
                week_start_date=week_start,
                total_hours=0,
                status=TimesheetStatus.MISSED,
                submitted_at=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                entries=[],
            )
            await self._timesheets.save(missed)
            flagged += 1
        return flagged
