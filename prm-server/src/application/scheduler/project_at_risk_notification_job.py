from src.application.ai.risk_summary_use_case import RiskSummaryUseCase
from src.application.dtos.ai_dtos import RiskSummaryRequest
from src.application.notifications.email_notification_service import EmailNotificationService
from src.domain.enums import MilestoneStatus, NotificationType, ProjectHealthStatus
from src.domain.ports.ai_provider import IAIProvider
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    IMilestoneRepository,
    IProjectHealthRepository,
    IProjectRepository,
    IUserRepository,
)
from src.infrastructure.email.templates import project_at_risk_html

_HEALTH_COLORS = {
    ProjectHealthStatus.ON_TRACK: ("On Track", "#22c55e"),
    ProjectHealthStatus.ATTENTION: ("Attention", "#f59e0b"),
    ProjectHealthStatus.AT_RISK: ("At Risk", "#ef4444"),
}


class ProjectAtRiskNotificationJob:

    def __init__(
        self,
        projects: IProjectRepository,
        milestones: IMilestoneRepository,
        allocations: IAllocationRepository,
        employees: IEmployeeRepository,
        users: IUserRepository,
        health_repo: IProjectHealthRepository,
        risk_summary: RiskSummaryUseCase,
        email_service: EmailNotificationService,
    ) -> None:
        self._projects = projects
        self._milestones = milestones
        self._allocations = allocations
        self._employees = employees
        self._users = users
        self._health = health_repo
        self._risk_summary = risk_summary
        self._email = email_service

    async def run(self, project_ids: list[int]) -> int:
        sent = 0
        for project_id in project_ids:
            if await self._notify_project(project_id):
                sent += 1
        return sent

    async def _notify_project(self, project_id: int) -> bool:
        project = await self._projects.find_by_id(project_id)
        if project is None or project.id is None:
            return False
        manager = await self._users.find_by_id(project.manager_user_id)
        if manager is None or manager.id is None or not manager.email:
            return False

        snapshot = await self._health.find_latest_by_project(project.id)
        health = snapshot.health_status if snapshot else ProjectHealthStatus.AT_RISK
        label, color = _HEALTH_COLORS.get(health, ("At Risk", "#ef4444"))

        milestones = await self._milestones.find_by_project(project.id)
        ms_lines = [
            f"<li>{m.title} — {m.status.value}"
            + (f" (due {m.due_date})" if m.due_date else "")
            + "</li>"
            for m in milestones
            if m.status not in (MilestoneStatus.DONE, MilestoneStatus.CANCELLED)
        ]
        milestones_html = (
            "<ul>" + "".join(ms_lines[:8]) + "</ul>" if ms_lines else "<p>None open.</p>"
        )

        summary_result = await self._risk_summary.execute(
            project.manager_user_id,
            RiskSummaryRequest(project_id=project.id),
        )
        risk_text = summary_result.summary

        suggestions = await self._bench_suggestions(project.manager_user_id)
        suggested_html = (
            "<ul>" + "".join(f"<li>{s}</li>" for s in suggestions) + "</ul>"
            if suggestions
            else "<p>No bench resources with matching skills found.</p>"
        )

        ref = snapshot.computed_at.isoformat() if snapshot and snapshot.computed_at else str(
            project.id
        )
        return await self._email.send_if_new(
            NotificationType.PROJECT_AT_RISK,
            manager.id,
            manager.email,
            project.id,
            ref,
            f"Project at risk: {project.name}",
            project_at_risk_html(
                project.name,
                manager.full_name,
                label,
                color,
                milestones_html,
                risk_text,
                suggested_html,
            ),
        )

    async def _bench_suggestions(self, manager_user_id: int) -> list[str]:
        team = await self._employees.find_by_manager(manager_user_id)
        suggestions: list[str] = []
        for emp in team:
            if emp.id is None:
                continue
            active = await self._allocations.find_active_by_employee(emp.id)
            if sum(a.utilization_percent for a in active) > 0:
                continue
            skills = await self._employees.find_skills(emp.id)
            if not skills:
                continue
            user = await self._users.find_by_id(emp.user_id)
            name = user.full_name if user else emp.full_name
            skill_list = ", ".join(s.skill_name for s in skills[:6])
            suggestions.append(f"{name} — {skill_list}")
        return suggestions[:8]
