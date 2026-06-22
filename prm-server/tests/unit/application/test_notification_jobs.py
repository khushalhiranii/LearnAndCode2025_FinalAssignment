"""Unit tests for notification jobs and email service."""

from datetime import date, datetime, timezone

import pytest

from src.application.notifications.email_notification_service import EmailNotificationService
from src.application.scheduler.timesheet_reminder_job import TimesheetReminderJob, prior_monday
from src.domain.entities.notification import NotificationLog
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.entities.user import User
from src.domain.enums import NotificationType, TimesheetStatus
from src.domain.ports.email_provider import EmailMessage, IEmailProvider
from src.infrastructure.email.console_adapter import ConsoleEmailProvider
from tests.conftest import InMemoryAllocationRepository, InMemoryEmployeeRepository, make_allocation
from tests.unit.application.test_scheduler_jobs import InMemoryTimesheetRepository


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self.logs: list[NotificationLog] = []
        self.tracking: dict[tuple[int, str], int] = {}

    async def was_sent(self, ntype, recipient_user_id, subject_id, reference_key) -> bool:
        return any(
            l.notification_type == ntype
            and l.recipient_user_id == recipient_user_id
            and l.subject_id == subject_id
            and l.reference_key == reference_key
            for l in self.logs
        )

    async def record_sent(self, log: NotificationLog) -> NotificationLog:
        log.id = len(self.logs) + 1
        self.logs.append(log)
        return log

    async def get_reminder_tracking(self, resource_profile_id, week_start_date):
        key = (resource_profile_id, week_start_date.isoformat())
        count = self.tracking.get(key)
        if count is None:
            return None
        from src.domain.entities.notification import TimesheetReminderTracking

        return TimesheetReminderTracking(
            id=1,
            resource_profile_id=resource_profile_id,
            week_start_date=week_start_date.isoformat(),
            reminder_count=count,
            last_reminder_sent_at=None,
        )

    async def save_reminder_tracking(self, tracking):
        key = (tracking.resource_profile_id, tracking.week_start_date)
        self.tracking[key] = tracking.reminder_count
        return tracking


class InMemoryUserRepository:
    def __init__(self, user: User) -> None:
        self._user = user

    async def find_by_id(self, user_id: int) -> User | None:
        return self._user if self._user.id == user_id else None


@pytest.mark.asyncio
async def test_timesheet_reminder_sends_on_tuesday() -> None:
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    ts_repo = InMemoryTimesheetRepository()
    notif_repo = InMemoryNotificationRepository()
    now = datetime.now(timezone.utc)
    user = User(
        id=5, full_name="Alice", email="alice@test.com", username="alice",
        password_hash="x", is_account_enabled=True, force_password_change=False,
        created_at=now, updated_at=now,
    )
    user_repo = InMemoryUserRepository(user)
    emp = ResourceProfile(
        id=1, user_id=5, full_name="Alice", email="alice@test.com",
        department=None, designation=None, date_of_joining=None,
        manager_user_id=2, is_available=True, created_at=now, updated_at=now,
    )
    await emp_repo.save(emp)
    week = prior_monday()
    await alloc_repo.save(make_allocation(resource_profile_id=1))

    email_svc = EmailNotificationService(ConsoleEmailProvider(), notif_repo)
    job = TimesheetReminderJob(
        emp_repo, alloc_repo, ts_repo, user_repo, notif_repo, email_svc
    )
    tuesday = week + __import__("datetime").timedelta(days=8)
    stats = await job.run(today=tuesday)
    assert stats["reminders"] == 1
    assert len(notif_repo.logs) == 1
    assert notif_repo.logs[0].notification_type == NotificationType.TIMESHEET_REMINDER_1.value


@pytest.mark.asyncio
async def test_timesheet_freeze_on_thursday() -> None:
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    ts_repo = InMemoryTimesheetRepository()
    notif_repo = InMemoryNotificationRepository()
    now = datetime.now(timezone.utc)
    user = User(
        id=5, full_name="Alice", email="alice@test.com", username="alice",
        password_hash="x", is_account_enabled=True, force_password_change=False,
        created_at=now, updated_at=now,
    )
    user_repo = InMemoryUserRepository(user)
    emp = ResourceProfile(
        id=1, user_id=5, full_name="Alice", email="alice@test.com",
        department=None, designation=None, date_of_joining=None,
        manager_user_id=2, is_available=True, created_at=now, updated_at=now,
    )
    await emp_repo.save(emp)
    week = prior_monday()
    await alloc_repo.save(make_allocation(resource_profile_id=1))

    email_svc = EmailNotificationService(ConsoleEmailProvider(), notif_repo)
    job = TimesheetReminderJob(
        emp_repo, alloc_repo, ts_repo, user_repo, notif_repo, email_svc
    )
    thursday = week + __import__("datetime").timedelta(days=10)
    stats = await job.run(today=thursday)
    assert stats["frozen"] == 1
    updated = await emp_repo.find_by_id(1)
    assert updated is not None
    assert updated.timesheet_frozen is True
    ts = await ts_repo.find_by_employee_and_week(1, week)
    assert ts is not None
    assert ts.status == TimesheetStatus.MISSED
