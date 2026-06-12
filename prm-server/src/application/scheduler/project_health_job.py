import json
from datetime import date, datetime, timezone

from src.domain.entities.project_health import ProjectHealthSnapshot
from src.domain.enums import MilestoneStatus, ProjectHealthStatus, ProjectStatus, TimesheetStatus
from src.domain.ports.repositories import (
    IAllocationRepository,
    IMilestoneRepository,
    IProjectHealthRepository,
    IProjectRepository,
    ISystemConfigRepository,
    ITimesheetRepository,
)


class ProjectHealthJob:

    def __init__(
        self,
        projects: IProjectRepository,
        milestones: IMilestoneRepository,
        allocations: IAllocationRepository,
        timesheets: ITimesheetRepository,
        health_repo: IProjectHealthRepository,
        system_config: ISystemConfigRepository,
    ) -> None:
        self._projects = projects
        self._milestones = milestones
        self._allocations = allocations
        self._timesheets = timesheets
        self._health = health_repo
        self._system_config = system_config

    async def run(self) -> int:
        today = date.today()
        prior_week = today - __import__("datetime").timedelta(days=today.weekday() + 7)
        config = await self._system_config.get_config()
        max_weekly_hours = config.max_weekly_hours

        projects, _ = await self._projects.find_all(
            status=ProjectStatus.ACTIVE, page=1, page_size=10000
        )
        count = 0
        for project in projects:
            if project.id is None:
                continue
            flags: list[str] = []
            status = ProjectHealthStatus.ON_TRACK

            project_milestones = await self._milestones.find_by_project(project.id)
            for ms in project_milestones:
                if (
                    ms.due_date
                    and ms.due_date < today
                    and ms.status
                    not in (MilestoneStatus.DONE, MilestoneStatus.CANCELLED)
                ):
                    flags.append(
                        f"Milestone '{ms.title}' is overdue (due {ms.due_date})"
                    )
                    status = ProjectHealthStatus.AT_RISK

            active_allocs = await self._allocations.find_by_project(
                project.id, active_only=True
            )
            for alloc in active_allocs:
                ts = await self._timesheets.find_by_employee_and_week(
                    alloc.resource_profile_id, prior_week
                )
                expected = (alloc.utilization_percent / 100) * max_weekly_hours
                logged = (
                    ts.total_hours
                    if ts and ts.status == TimesheetStatus.SUBMITTED
                    else 0
                )
                if expected > 0 and logged < expected * 0.5:
                    flags.append(
                        f"Resource profile {alloc.resource_profile_id} logged "
                        f"{logged}h last week (expected ~{expected:.0f}h)"
                    )
                    if status != ProjectHealthStatus.AT_RISK:
                        status = ProjectHealthStatus.ATTENTION

            snapshot = ProjectHealthSnapshot(
                id=None,
                project_id=project.id,
                health_status=status,
                risk_flags_json=json.dumps(flags),
                computed_at=datetime.now(timezone.utc),
            )
            await self._health.save_snapshot(snapshot)
            count += 1
        return count
