"""Unit tests for scheduler jobs."""

from datetime import date, datetime, timezone

import pytest

from src.application.scheduler.missed_timesheet_job import MissedTimesheetJob, _prior_monday
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.entities.timesheet import Timesheet
from src.domain.enums import TimesheetStatus
from tests.conftest import InMemoryAllocationRepository, InMemoryEmployeeRepository, make_allocation


class InMemoryTimesheetRepository:
    def __init__(self) -> None:
        self._store: list[Timesheet] = []
        self._next_id = 1

    async def find_by_employee_and_week(self, employee_id, week_start):
        for ts in self._store:
            if ts.resource_profile_id == employee_id and ts.week_start_date == week_start:
                return ts
        return None

    async def save(self, timesheet: Timesheet) -> Timesheet:
        if timesheet.id is None:
            timesheet.id = self._next_id
            self._next_id += 1
        self._store.append(timesheet)
        return timesheet

    async def find_by_id(self, tid): return None
    async def find_by_employee(self, eid): return self._store


@pytest.mark.asyncio
async def test_missed_timesheet_job_flags_missing_submission() -> None:
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    ts_repo = InMemoryTimesheetRepository()

    now = datetime.now(timezone.utc)
    emp = ResourceProfile(
        id=1, user_id=5, full_name="E", email="e@t.com",
        department=None, designation=None, date_of_joining=None,
        manager_user_id=2, is_available=True, created_at=now, updated_at=now,
    )
    await emp_repo.save(emp)
    week = _prior_monday()
    await alloc_repo.save(make_allocation(resource_profile_id=1))

    job = MissedTimesheetJob(emp_repo, alloc_repo, ts_repo)
    count = await job.run()
    assert count == 1
    saved = await ts_repo.find_by_employee_and_week(1, week)
    assert saved is not None
    assert saved.status == TimesheetStatus.MISSED
