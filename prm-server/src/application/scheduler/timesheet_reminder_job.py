from datetime import date, datetime, timedelta, timezone

from src.application.notifications.email_notification_service import EmailNotificationService
from src.domain.entities.notification import TimesheetReminderTracking
from src.domain.entities.timesheet import Timesheet
from src.domain.enums import NotificationType, TimesheetStatus
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    INotificationRepository,
    ITimesheetRepository,
    IUserRepository,
)
from src.infrastructure.email.templates import timesheet_frozen_html, timesheet_reminder_html


def prior_monday(reference: date | None = None) -> date:
    today = reference or date.today()
    this_monday = today - timedelta(days=today.weekday())
    return this_monday - timedelta(days=7)


def _is_submitted(timesheet) -> bool:
    return timesheet is not None and timesheet.status == TimesheetStatus.SUBMITTED


class TimesheetReminderJob:
    """
    Weekday escalation: Tue reminder 1, Wed reminder 2, Thu freeze + notify.
  Prior week timesheet; deadline end of Monday.
    """

    def __init__(
        self,
        employees: IEmployeeRepository,
        allocations: IAllocationRepository,
        timesheets: ITimesheetRepository,
        users: IUserRepository,
        notifications: INotificationRepository,
        email_service: EmailNotificationService,
    ) -> None:
        self._employees = employees
        self._allocations = allocations
        self._timesheets = timesheets
        self._users = users
        self._notifications = notifications
        self._email = email_service

    async def run(self, today: date | None = None) -> dict[str, int]:
        today = today or date.today()
        if today.weekday() >= 5:
            return {"reminders": 0, "frozen": 0}

        week_start = prior_monday(today)
        weekday = today.weekday()
        stats = {"reminders": 0, "frozen": 0}

        employees, _ = await self._employees.find_all(is_active=True, page=1, page_size=10000)
        for emp in employees:
            if emp.id is None:
                continue
            allocs = await self._allocations.find_active_by_employee_and_week(emp.id, week_start)
            if not allocs:
                continue
            ts = await self._timesheets.find_by_employee_and_week(emp.id, week_start)
            if _is_submitted(ts):
                continue

            user = await self._users.find_by_id(emp.user_id)
            emp_name = user.full_name if user else emp.full_name
            emp_email = user.email if user else ""

            tracking = await self._notifications.get_reminder_tracking(emp.id, week_start)
            reminder_count = tracking.reminder_count if tracking else 0

            if weekday == 1 and reminder_count < 1:
                sent = await self._send_reminder(
                    emp, emp_name, emp_email, week_start, reminder_count, 1
                )
                if sent:
                    stats["reminders"] += 1
            elif weekday == 2 and reminder_count < 2:
                sent = await self._send_reminder(
                    emp, emp_name, emp_email, week_start, reminder_count, 2
                )
                if sent:
                    stats["reminders"] += 1
            elif weekday >= 3 and not emp.timesheet_frozen:
                await self._freeze_and_notify(emp, emp_name, emp_email, week_start, ts)
                stats["frozen"] += 1

        return stats

    async def _send_reminder(
        self,
        emp,
        name: str,
        email: str,
        week_start: date,
        current_count: int,
        number: int,
    ) -> bool:
        ntype = (
            NotificationType.TIMESHEET_REMINDER_1
            if number == 1
            else NotificationType.TIMESHEET_REMINDER_2
        )
        ref = week_start.isoformat()
        sent = await self._email.send_if_new(
            ntype,
            emp.user_id,
            email,
            emp.id,
            ref,
            f"Timesheet reminder #{number} — week of {week_start}",
            timesheet_reminder_html(name, ref, number),
        )
        if sent:
            now = datetime.now(timezone.utc)
            await self._notifications.save_reminder_tracking(
                TimesheetReminderTracking(
                    id=None,
                    resource_profile_id=emp.id,
                    week_start_date=ref,
                    reminder_count=number,
                    last_reminder_sent_at=now,
                )
            )
        return sent

    async def _freeze_and_notify(self, emp, name: str, email: str, week_start: date, ts) -> None:
        now = datetime.now(timezone.utc)
        if ts is None or ts.status != TimesheetStatus.MISSED:
            missed = Timesheet(
                id=None,
                resource_profile_id=emp.id,
                week_start_date=week_start,
                total_hours=0,
                status=TimesheetStatus.MISSED,
                submitted_at=None,
                created_at=now,
                updated_at=now,
                entries=[],
            )
            await self._timesheets.save(missed)

        await self._employees.update_timesheet_freeze(emp.id, True, now, week_start)
        ref = week_start.isoformat()

        await self._email.send_if_new(
            NotificationType.TIMESHEET_FROZEN,
            emp.user_id,
            email,
            emp.id,
            ref,
            f"Timesheet submission frozen — week of {week_start}",
            timesheet_frozen_html(name, ref, for_manager=False),
        )

        if emp.manager_user_id:
            manager = await self._users.find_by_id(emp.manager_user_id)
            if manager and manager.id is not None:
                await self._email.send_if_new(
                    NotificationType.TIMESHEET_FROZEN,
                    manager.id,
                    manager.email,
                    emp.id,
                    ref,
                    f"Employee timesheet frozen: {name}",
                    timesheet_frozen_html(name, ref, for_manager=True),
                )
