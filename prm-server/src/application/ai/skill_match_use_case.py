from datetime import datetime, timezone

from src.application.dtos.ai_dtos import SkillMatchItemResponse, SkillMatchRequest, SkillMatchResponse
from src.domain.entities.project_health import AISuggestionAudit
from src.domain.enums import AIRequestType
from src.domain.exceptions import AuthorizationError
from src.domain.ports.ai_provider import IAIProvider, SkillMatchCandidate
from src.domain.ports.repositories import (
    IAISuggestionAuditRepository,
    IAllocationRepository,
    IEmployeeRepository,
    IProjectRepository,
    ITimesheetRepository,
    IUserRepository,
)


class SkillMatchUseCase:

    def __init__(
        self,
        employees: IEmployeeRepository,
        allocations: IAllocationRepository,
        timesheets: ITimesheetRepository,
        users: IUserRepository,
        projects: IProjectRepository,
        ai_provider: IAIProvider,
        audit_repo: IAISuggestionAuditRepository,
    ) -> None:
        self._employees = employees
        self._allocations = allocations
        self._timesheets = timesheets
        self._users = users
        self._projects = projects
        self._ai = ai_provider
        self._audit = audit_repo

    async def execute(
        self, manager_user_id: int, request: SkillMatchRequest
    ) -> SkillMatchResponse:
        if request.project_id is not None:
            project = await self._projects.find_by_id(request.project_id)
            if project is None or project.manager_user_id != manager_user_id:
                raise AuthorizationError("You can only search resources for your own projects.")

        team = await self._employees.find_by_manager(manager_user_id)
        needed_util = request.utilization_percent or (
            int((request.hours_per_week or 40) / 40 * 100) if request.hours_per_week else 100
        )

        candidates: list[SkillMatchCandidate] = []
        for emp in team:
            if emp.id is None:
                continue
            active = await self._allocations.find_active_by_employee(emp.id)
            used = sum(a.utilization_percent for a in active)
            free = 100 - used
            if free < needed_util:
                continue

            skills = await self._employees.find_skills(emp.id)
            skill_names = [s.skill_name for s in skills]
            recent_tags: list[str] = []
            history = await self._timesheets.find_by_employee(emp.id)
            for ts in history[:3]:
                detail = await self._timesheets.find_by_id(ts.id) if ts.id else None
                if detail:
                    for entry in detail.entries:
                        recent_tags.extend(t.tag_name for t in entry.tags)

            user = await self._users.find_by_id(emp.user_id)
            candidates.append(
                SkillMatchCandidate(
                    resource_profile_id=emp.id,
                    full_name=user.full_name if user else emp.full_name,
                    skills=skill_names,
                    utilization_percent=used,
                    free_percent=free,
                    recent_activity_tags=list(dict.fromkeys(recent_tags))[:10],
                    work_status="BENCH" if used == 0 else "ALLOCATED",
                )
            )

        if not candidates:
            return SkillMatchResponse(
                query=request.query,
                matches=[],
                ai_generated=False,
                note="No team members have sufficient free capacity for this request.",
            )

        results = await self._ai.rank_resources(
            request.query, candidates, request.hours_per_week
        )
        by_id = {c.resource_profile_id: c for c in candidates}
        matches = [
            SkillMatchItemResponse(
                rank=r.rank,
                resource_profile_id=r.resource_profile_id,
                full_name=r.full_name,
                reason=r.reason,
                free_percent=by_id[r.resource_profile_id].free_percent
                if r.resource_profile_id in by_id
                else 0,
            )
            for r in results
        ]

        await self._audit.save(
            AISuggestionAudit(
                id=None,
                request_type=AIRequestType.SKILL_MATCH.value,
                subject_id=request.project_id or manager_user_id,
                input_summary=request.query[:500],
                response_summary=str([m.model_dump() for m in matches])[:2000],
                provider=self._ai.provider_name,
                created_at=datetime.now(timezone.utc),
            )
        )

        return SkillMatchResponse(
            query=request.query,
            matches=matches,
            ai_generated=True,
        )
