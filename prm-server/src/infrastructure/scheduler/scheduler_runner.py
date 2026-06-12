import asyncio
import threading

import structlog

from src.infrastructure.database.engine import AsyncSessionFactory
from src.infrastructure.unit_of_work import UnitOfWork
from src.application.scheduler.missed_timesheet_job import MissedTimesheetJob
from src.application.scheduler.project_health_job import ProjectHealthJob

log = structlog.get_logger()


class SchedulerRunner:
    """Runs scheduler jobs on a daemon background thread."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._reschedule_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval_minutes = 240

    def start(self, interval_minutes: int = 240) -> None:
        self._interval_minutes = max(1, interval_minutes)
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="prm-scheduler")
        self._thread.start()
        log.info("scheduler_started", interval_minutes=self._interval_minutes)

    def stop(self) -> None:
        self._stop_event.set()
        self._reschedule_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        log.info("scheduler_stopped")

    def reschedule(self, interval_minutes: int) -> None:
        """Apply a new interval; the running loop picks it up within ~1 second."""
        self._interval_minutes = max(1, interval_minutes)
        self._reschedule_event.set()
        log.info("scheduler_rescheduled", interval_minutes=self._interval_minutes)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                asyncio.run(self._run_jobs())
            except Exception as exc:
                log.error("scheduler_job_failed", error=str(exc))

            waited_seconds = 0
            target_seconds = self._interval_minutes * 60
            while waited_seconds < target_seconds and not self._stop_event.is_set():
                if self._reschedule_event.is_set():
                    self._reschedule_event.clear()
                    waited_seconds = 0
                    target_seconds = self._interval_minutes * 60
                    continue
                if self._stop_event.wait(timeout=1.0):
                    return
                waited_seconds += 1

    async def _run_jobs(self) -> None:
        async with AsyncSessionFactory() as session:
            uow = UnitOfWork(session)
            missed_job = MissedTimesheetJob(uow.employees, uow.allocations, uow.timesheets)
            health_job = ProjectHealthJob(
                uow.projects,
                uow.milestones,
                uow.allocations,
                uow.timesheets,
                uow.project_health,
                uow.system_config,
            )
            missed = await missed_job.run()
            health = await health_job.run()
            await uow.commit()
            log.info("scheduler_jobs_complete", missed_timesheets=missed, health_snapshots=health)


_scheduler: SchedulerRunner | None = None


def get_scheduler() -> SchedulerRunner:
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerRunner()
    return _scheduler
