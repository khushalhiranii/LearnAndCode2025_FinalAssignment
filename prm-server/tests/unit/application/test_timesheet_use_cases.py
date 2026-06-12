from datetime import date, datetime, timezone

import pytest

from src.application.dtos.timesheet_dtos import (
    SubmitTimesheetRequest,
    TimesheetEntryRequest,
    TimesheetEntryTagRequest,
)
from src.application.employee.timesheet_use_case import EmployeeTimesheetUseCase
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.entities.system_config import SystemConfig
from src.domain.entities.timesheet import ActivityTag, Timesheet
from src.domain.enums import TimesheetStatus
from src.domain.exceptions import (
    DuplicateTimesheetError,
    FutureWeekError,
    HoursCapExceededError,
    ProjectNotAllocatedError,
)
from tests.conftest import (
    InMemoryAllocationRepository,
    InMemoryEmployeeRepository,
    make_allocation,
)


class InMemoryTimesheetRepository:
    def __init__(self) -> None:
        self._store: dict[tuple[int, date], Timesheet] = {}
        self._next_id = 1

    async def find_by_id(self, timesheet_id: int):
        return None

    async def find_by_employee_and_week(self, employee_id: int, week_start: date):
        return self._store.get((employee_id, week_start))

    async def find_by_employee(self, employee_id: int):
        return [ts for (eid, _), ts in self._store.items() if eid == employee_id]

    async def save(self, timesheet: Timesheet) -> Timesheet:
        if timesheet.id is None:
            timesheet.id = self._next_id
            self._next_id += 1
        self._store[(timesheet.resource_profile_id, timesheet.week_start_date)] = timesheet
        return timesheet


class InMemoryActivityTagRepository:
    def __init__(self, tags: list[ActivityTag]) -> None:
        self._tags = {t.id: t for t in tags if t.id is not None}

    async def find_all_active(self):
        return list(self._tags.values())

    async def find_by_ids(self, ids: list[int]):
        return [self._tags[i] for i in ids if i in self._tags]


class InMemorySystemConfigRepository:
    def __init__(self, max_weekly_hours: int = 40) -> None:
        self._config = SystemConfig(
            llm_provider="mock",
            llm_api_key="",
            llm_base_url="",
            llm_model="",
            scheduler_interval_minutes=240,
            max_weekly_hours=max_weekly_hours,
        )

    async def get_config(self) -> SystemConfig:
        return self._config

    async def update_config(self, config: SystemConfig) -> SystemConfig:
        self._config = config
        return config


def _make_use_case(
    employee_repo: InMemoryEmployeeRepository,
    allocation_repo: InMemoryAllocationRepository,
    timesheet_repo: InMemoryTimesheetRepository | None = None,
) -> EmployeeTimesheetUseCase:
    now = datetime.now(timezone.utc)
    tags = [ActivityTag(id=1, name="Development", category="DEVELOPMENT", is_system_tag=True, is_active=True)]
    return EmployeeTimesheetUseCase(
        timesheet_repo or InMemoryTimesheetRepository(),
        employee_repo,
        InMemoryActivityTagRepository(tags),
        allocation_repo,
        InMemorySystemConfigRepository(max_weekly_hours=40),
    )


async def _seed_employee(repo: InMemoryEmployeeRepository, user_id: int = 5, employee_id: int = 10):
    now = datetime.now(timezone.utc)
    profile = ResourceProfile(
        id=employee_id,
        user_id=user_id,
        full_name="Test User",
        email="test@test.local",
        department=None,
        designation=None,
        date_of_joining=None,
        manager_user_id=2,
        is_available=True,
        created_at=now,
        updated_at=now,
    )
    await repo.save(profile)
    return profile


@pytest.mark.asyncio
async def test_submit_timesheet_success_within_allocation_cap():
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    await _seed_employee(emp_repo)
    await alloc_repo.save(
        make_allocation(
            resource_profile_id=10,
            project_id=1,
            utilization_percent=100,
        )
    )
    use_case = _make_use_case(emp_repo, alloc_repo)

    week = date(2026, 6, 9)
    request = SubmitTimesheetRequest(
        week_start_date=week,
        entries=[
            TimesheetEntryRequest(
                project_id=1,
                hours_worked=40.0,
                tags=[TimesheetEntryTagRequest(activity_tag_id=1)],
            )
        ],
    )
    result = await use_case.submit_timesheet(5, request)
    assert result.total_hours == 40.0
    assert result.status == TimesheetStatus.SUBMITTED


@pytest.mark.asyncio
async def test_submit_timesheet_rejects_unallocated_project():
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    await _seed_employee(emp_repo)
    use_case = _make_use_case(emp_repo, alloc_repo)

    request = SubmitTimesheetRequest(
        week_start_date=date(2026, 6, 9),
        entries=[
            TimesheetEntryRequest(
                project_id=99,
                hours_worked=8.0,
                tags=[TimesheetEntryTagRequest(activity_tag_id=1)],
            )
        ],
    )
    with pytest.raises(ProjectNotAllocatedError):
        await use_case.submit_timesheet(5, request)


@pytest.mark.asyncio
async def test_submit_timesheet_rejects_hours_above_project_cap():
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    await _seed_employee(emp_repo)
    await alloc_repo.save(
        make_allocation(resource_profile_id=10, project_id=1, utilization_percent=50)
    )
    use_case = _make_use_case(emp_repo, alloc_repo)

    request = SubmitTimesheetRequest(
        week_start_date=date(2026, 6, 9),
        entries=[
            TimesheetEntryRequest(
                project_id=1,
                hours_worked=25.0,
                tags=[TimesheetEntryTagRequest(activity_tag_id=1)],
            )
        ],
    )
    with pytest.raises(HoursCapExceededError):
        await use_case.submit_timesheet(5, request)


@pytest.mark.asyncio
async def test_submit_timesheet_rejects_future_week():
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    await _seed_employee(emp_repo)
    use_case = _make_use_case(emp_repo, alloc_repo)

    request = SubmitTimesheetRequest(
        week_start_date=date(2099, 1, 5),
        entries=[
            TimesheetEntryRequest(
                project_id=1,
                hours_worked=8.0,
                tags=[TimesheetEntryTagRequest(activity_tag_id=1)],
            )
        ],
    )
    with pytest.raises(FutureWeekError):
        await use_case.submit_timesheet(5, request)


@pytest.mark.asyncio
async def test_submit_timesheet_rejects_duplicate_week():
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    ts_repo = InMemoryTimesheetRepository()
    await _seed_employee(emp_repo)
    await alloc_repo.save(make_allocation(resource_profile_id=10, project_id=1))
    week = date(2026, 6, 9)
    ts_repo._store[(10, week)] = Timesheet(
        id=1,
        resource_profile_id=10,
        week_start_date=week,
        total_hours=40,
        status=TimesheetStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        entries=[],
    )
    use_case = _make_use_case(emp_repo, alloc_repo, ts_repo)

    request = SubmitTimesheetRequest(
        week_start_date=week,
        entries=[
            TimesheetEntryRequest(
                project_id=1,
                hours_worked=8.0,
                tags=[TimesheetEntryTagRequest(activity_tag_id=1)],
            )
        ],
    )
    with pytest.raises(DuplicateTimesheetError):
        await use_case.submit_timesheet(5, request)
