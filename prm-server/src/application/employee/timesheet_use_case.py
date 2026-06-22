from datetime import date, datetime, timezone
from typing import Any

from src.application.dtos.timesheet_dtos import (
    ActivityTagResponse,
    SubmitTimesheetRequest,
    TimesheetResponse,
    TimesheetEntryDTO,
    TimesheetEntryTagDTO,
)
from src.domain.entities.timesheet import Timesheet, TimesheetEntry, TimesheetEntryTag
from src.domain.enums import TimesheetStatus
from src.domain.ports.repositories import (
    IActivityTagRepository,
    IAllocationRepository,
    IEmployeeRepository,
    ISystemConfigRepository,
    ITimesheetRepository,
)
from src.domain.exceptions import (
    DuplicateTimesheetError,
    EmployeeNotFoundError,
    FutureWeekError,
    HoursCapExceededError,
    InvalidActivityTagError,
    ProjectNotAllocatedError,
    TimesheetSubmissionFrozenError,
)


def _to_response(timesheet: Timesheet) -> TimesheetResponse:
    entries = []
    for e in timesheet.entries:
        tags = [
            TimesheetEntryTagDTO(
                activity_tag_id=t.activity_tag_id,
                tag_name=t.tag_name,
                custom_tag_text=t.custom_tag_text,
            )
            for t in e.tags
        ]
        entries.append(
            TimesheetEntryDTO(
                id=e.id or 0,
                project_id=e.project_id,
                hours_worked=e.hours_worked,
                tags=tags,
            )
        )

    return TimesheetResponse(
        id=timesheet.id or 0,
        resource_profile_id=timesheet.resource_profile_id,
        week_start_date=timesheet.week_start_date,
        total_hours=timesheet.total_hours,
        status=timesheet.status,
        submitted_at=timesheet.submitted_at,
        entries=entries,
    )


class EmployeeTimesheetUseCase:

    def __init__(
        self,
        timesheet_repo: ITimesheetRepository,
        employee_repo: IEmployeeRepository,
        activity_tag_repo: IActivityTagRepository,
        allocation_repo: IAllocationRepository,
        system_config_repo: ISystemConfigRepository,
    ) -> None:
        self._timesheets = timesheet_repo
        self._employees = employee_repo
        self._activity_tags = activity_tag_repo
        self._allocations = allocation_repo
        self._system_config = system_config_repo

    async def list_activity_tags(self) -> list[ActivityTagResponse]:
        tags = await self._activity_tags.find_all_active()
        return [
            ActivityTagResponse(
                id=t.id,  # type: ignore[arg-type]
                name=t.name,
                category=t.category,
            )
            for t in tags
            if t.id is not None
        ]

    async def list_my_timesheets(self, employee_user_id: int) -> list[TimesheetResponse]:
        employee = await self._employees.find_by_user_id(employee_user_id)
        if not employee:
            return []

        timesheets = await self._timesheets.find_by_employee(employee.id)
        return [_to_response(ts) for ts in timesheets]

    async def submit_timesheet(
        self,
        employee_user_id: int,
        request: SubmitTimesheetRequest,
    ) -> TimesheetResponse:
        employee = await self._employees.find_by_user_id(employee_user_id)
        if not employee:
            raise EmployeeNotFoundError("Employee profile not found.")
        if employee.timesheet_frozen:
            raise TimesheetSubmissionFrozenError(
                "Timesheet submission is frozen. Contact your manager to restore access."
            )

        today = date.today()
        if request.week_start_date > today:
            raise FutureWeekError("Cannot submit timesheets for future weeks.")

        existing = await self._timesheets.find_by_employee_and_week(
            employee.id, request.week_start_date
        )
        if existing:
            raise DuplicateTimesheetError(
                "Timesheet for this week has already been submitted."
            )

        config = await self._system_config.get_config()
        max_weekly_hours = config.max_weekly_hours

        active_allocations = await self._allocations.find_active_by_employee_and_week(
            employee.id, request.week_start_date
        )
        alloc_by_project = {
            a.project_id: a.utilization_percent for a in active_allocations
        }

        hours_by_project: dict[int, float] = {}
        for entry in request.entries:
            hours_by_project[entry.project_id] = (
                hours_by_project.get(entry.project_id, 0) + entry.hours_worked
            )

        total_hours = sum(hours_by_project.values())
        if total_hours > max_weekly_hours:
            raise HoursCapExceededError(
                f"Total hours ({total_hours}) exceed the configured maximum "
                f"of {max_weekly_hours} hours per week."
            )

        for project_id, hours in hours_by_project.items():
            if project_id not in alloc_by_project:
                raise ProjectNotAllocatedError(
                    f"No active allocation for project {project_id} during this week."
                )
            project_cap = alloc_by_project[project_id] * max_weekly_hours / 100
            if hours > project_cap:
                raise HoursCapExceededError(
                    f"Hours logged for project {project_id} ({hours}) exceed the "
                    f"allocation cap of {project_cap:.2f} hours "
                    f"({alloc_by_project[project_id]}% of {max_weekly_hours}h)."
                )

        tag_ids = [t.activity_tag_id for e in request.entries for t in e.tags]
        valid_tags: dict[int, str] = {}
        if tag_ids:
            tags_list = await self._activity_tags.find_by_ids(list(set(tag_ids)))
            valid_tags = {t.id: t.name for t in tags_list if t.id is not None}

        entries = []
        for e in request.entries:
            entry_tags = []
            for t in e.tags:
                if t.activity_tag_id not in valid_tags:
                    raise InvalidActivityTagError(
                        f"Invalid activity tag ID: {t.activity_tag_id}"
                    )
                entry_tags.append(
                    TimesheetEntryTag(
                        activity_tag_id=t.activity_tag_id,
                        tag_name=valid_tags[t.activity_tag_id],
                        custom_tag_text=t.custom_tag_text,
                    )
                )

            entries.append(
                TimesheetEntry(
                    id=None,
                    timesheet_id=None,
                    project_id=e.project_id,
                    hours_worked=e.hours_worked,
                    tags=entry_tags,
                    created_at=datetime.now(timezone.utc),
                )
            )

        now = datetime.now(timezone.utc)
        timesheet = Timesheet(
            id=None,
            resource_profile_id=employee.id,
            week_start_date=request.week_start_date,
            total_hours=total_hours,
            status=TimesheetStatus.SUBMITTED,
            submitted_at=now,
            created_at=now,
            updated_at=now,
            entries=entries,
        )

        saved = await self._timesheets.save(timesheet)
        return _to_response(saved)
