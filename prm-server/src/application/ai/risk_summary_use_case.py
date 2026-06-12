import json
from datetime import date, timedelta

from src.application.dtos.ai_dtos import RiskSummaryRequest, RiskSummaryResponse
from src.domain.entities.project_health import AISuggestionAudit
from src.domain.enums import AIRequestType, MilestoneStatus
from src.domain.exceptions import AuthorizationError, ProjectNotFoundError
from src.domain.ports.ai_provider import IAIProvider, RiskSummaryContext
from src.domain.ports.repositories import (
    IAISuggestionAuditRepository,
    IAllocationRepository,
    IMilestoneRepository,
    IProjectHealthRepository,
    IProjectRepository,
    ITimesheetRepository,
)
from src.infrastructure.database.repositories.project_health_repository import parse_risk_flags


class RiskSummaryUseCase:

    def __init__(
        self,
        projects: IProjectRepository,
        milestones: IMilestoneRepository,
        allocations: IAllocationRepository,
        timesheets: ITimesheetRepository,
        health_repo: IProjectHealthRepository,
        ai_provider: IAIProvider,
        audit_repo: IAISuggestionAuditRepository,
    ) -> None:
        self._projects = projects
        self._milestones = milestones
        self._allocations = allocations
        self._timesheets = timesheets
        self._health = health_repo
        self._ai = ai_provider
        self._audit = audit_repo

    async def execute(
        self, manager_user_id: int, request: RiskSummaryRequest
    ) -> RiskSummaryResponse:
        project = await self._projects.find_by_id(request.project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {request.project_id} not found.")
        if project.manager_user_id != manager_user_id:
            raise AuthorizationError("You can only view risk summaries for your own projects.")

        today = date.today()
        prior_week = today - timedelta(days=today.weekday() + 7)
        ms_list = await self._milestones.find_by_project(project.id)  # type: ignore[arg-type]
        milestone_data = []
        flags: list[str] = []
        for ms in ms_list:
            overdue = (
                ms.due_date
                and ms.due_date < today
                and ms.status not in (MilestoneStatus.DONE, MilestoneStatus.CANCELLED)
            )
            if overdue:
                flags.append(f"{ms.title} is overdue")
            milestone_data.append(
                {
                    "title": ms.title,
                    "status": ms.status.value,
                    "due_date": str(ms.due_date) if ms.due_date else None,
                    "overdue": overdue,
                }
            )

        effort_data = []
        for alloc in await self._allocations.find_by_project(
            project.id, active_only=True  # type: ignore[arg-type]
        ):
            ts = await self._timesheets.find_by_employee_and_week(
                alloc.resource_profile_id, prior_week
            )
            expected = (alloc.utilization_percent / 100) * 40
            logged = ts.total_hours if ts else 0
            effort_data.append(
                {
                    "resource_profile_id": alloc.resource_profile_id,
                    "expected_hours": expected,
                    "logged_hours": float(logged),
                }
            )
            if expected > 0 and logged < expected * 0.5:
                flags.append(
                    f"Resource {alloc.resource_profile_id} logged only {logged}h "
                    f"(expected ~{expected:.0f}h)"
                )

        snapshot = await self._health.find_latest_by_project(project.id)  # type: ignore[arg-type]
        health_status = snapshot.health_status.value if snapshot else "ON_TRACK"
        if snapshot and snapshot.risk_flags_json:
            flags = list(dict.fromkeys(flags + parse_risk_flags(snapshot.risk_flags_json)))

        context = RiskSummaryContext(
            project_name=project.name,
            milestones=milestone_data,
            resource_effort=effort_data,
            health_status=health_status,
            risk_flags=flags,
        )

        ai_generated = True
        try:
            summary = await self._ai.summarize_risk(context)
        except Exception:
            ai_generated = False
            summary = _rule_based_summary(context)

        await self._audit.save(
            AISuggestionAudit(
                id=None,
                request_type=AIRequestType.RISK_SUMMARY.value,
                subject_id=project.id,  # type: ignore[arg-type]
                input_summary=project.name[:500],
                response_summary=summary[:2000],
                provider=self._ai.provider_name if ai_generated else "fallback",
                created_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
            )
        )

        return RiskSummaryResponse(
            project_id=project.id,  # type: ignore[arg-type]
            project_name=project.name,
            summary=summary,
            ai_generated=ai_generated,
            health_status=health_status,
            risk_flags=flags,
        )


def _rule_based_summary(context: RiskSummaryContext) -> str:
    if not context.risk_flags:
        return (
            f"Project '{context.project_name}' appears on track based on current "
            f"milestone and timesheet data."
        )
    concerns = "; ".join(context.risk_flags[:5])
    return (
        f"Project '{context.project_name}' has potential risks: {concerns}. "
        f"The manager should review milestone progress and team availability."
    )
