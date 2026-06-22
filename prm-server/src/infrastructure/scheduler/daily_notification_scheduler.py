import asyncio
import threading
from datetime import datetime, timedelta

import structlog

from src.application.ai.risk_summary_use_case import RiskSummaryUseCase
from src.application.notifications.email_notification_service import EmailNotificationService
from src.application.scheduler.project_at_risk_notification_job import (
    ProjectAtRiskNotificationJob,
)
from src.application.scheduler.project_health_job import ProjectHealthJob
from src.application.scheduler.timesheet_reminder_job import TimesheetReminderJob
from src.infrastructure.database.engine import AsyncSessionFactory
from src.infrastructure.email.email_provider_factory import EmailProviderFactory
from src.infrastructure.llm.ai_provider_factory import AIProviderFactory
from src.infrastructure.unit_of_work import UnitOfWork

log = structlog.get_logger()


def _seconds_until_next_weekday_hour(hour: int = 8) -> float:
    now = datetime.now()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if now.weekday() >= 5:
        days_ahead = 7 - now.weekday()
        target = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
    elif now >= target:
        target += timedelta(days=1)
        while target.weekday() >= 5:
            target += timedelta(days=1)
    return max(1.0, (target - now).total_seconds())


class DailyNotificationScheduler:

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="prm-daily-notifications"
        )
        self._thread.start()
        log.info("daily_notification_scheduler_started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        log.info("daily_notification_scheduler_stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            wait_secs = _seconds_until_next_weekday_hour(8)
            if self._stop_event.wait(timeout=wait_secs):
                return
            try:
                asyncio.run(self._run_timesheet_reminders())
            except Exception as exc:
                log.error("daily_notification_failed", error=str(exc))

    async def _run_timesheet_reminders(self) -> None:
        async with AsyncSessionFactory() as session:
            uow = UnitOfWork(session)
            email = EmailProviderFactory.create()
            email_svc = EmailNotificationService(email, uow.notifications)
            job = TimesheetReminderJob(
                uow.employees,
                uow.allocations,
                uow.timesheets,
                uow.users,
                uow.notifications,
                email_svc,
            )
            stats = await job.run()
            await uow.commit()
            log.info("timesheet_reminder_job_complete", **stats)


_daily_scheduler: DailyNotificationScheduler | None = None


def get_daily_scheduler() -> DailyNotificationScheduler:
    global _daily_scheduler
    if _daily_scheduler is None:
        _daily_scheduler = DailyNotificationScheduler()
    return _daily_scheduler


async def run_health_and_at_risk_notifications(uow: UnitOfWork) -> dict[str, int]:
    email = EmailProviderFactory.create()
    email_svc = EmailNotificationService(email, uow.notifications)
    health_job = ProjectHealthJob(
        uow.projects,
        uow.milestones,
        uow.allocations,
        uow.timesheets,
        uow.project_health,
        uow.system_config,
    )
    health_count, at_risk_ids = await health_job.run()
    at_risk_sent = 0
    if at_risk_ids:
        config = await uow.system_config.get_config()
        ai = AIProviderFactory.create(config)
        risk_uc = RiskSummaryUseCase(
            uow.projects,
            uow.milestones,
            uow.allocations,
            uow.timesheets,
            uow.project_health,
            ai,
            uow.ai_audit,
        )
        notify_job = ProjectAtRiskNotificationJob(
            uow.projects,
            uow.milestones,
            uow.allocations,
            uow.employees,
            uow.users,
            uow.project_health,
            risk_uc,
            email_svc,
        )
        at_risk_sent = await notify_job.run(at_risk_ids)
    return {
        "health_snapshots": health_count,
        "at_risk_notifications": at_risk_sent,
    }
