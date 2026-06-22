from datetime import datetime, timezone

from src.application.ai.team_builder_matcher import TeamMemberPool, TeamRoleSlot, match_team
from src.application.dtos.ai_dtos import (
    TeamBuilderRequest,
    TeamBuilderResponse,
    TeamRoleGapResponse,
    TeamRoleMatchResponse,
)
from src.domain.entities.project_health import AISuggestionAudit
from src.domain.enums import AIRequestType
from src.domain.exceptions import AuthorizationError, SkillNotFoundError
from src.domain.ports.repositories import (
    IAISuggestionAuditRepository,
    IAllocationRepository,
    IEmployeeRepository,
    IProjectRepository,
    ISkillRepository,
)


class TeamBuilderUseCase:

    def __init__(
        self,
        employees: IEmployeeRepository,
        allocations: IAllocationRepository,
        skills: ISkillRepository,
        projects: IProjectRepository,
        audit_repo: IAISuggestionAuditRepository,
    ) -> None:
        self._employees = employees
        self._allocations = allocations
        self._skills = skills
        self._projects = projects
        self._audit = audit_repo

    async def execute(
        self,
        manager_user_id: int,
        request: TeamBuilderRequest,
        *,
        audit_input: str | None = None,
        audit_provider: str | None = None,
    ) -> TeamBuilderResponse:
        if request.project_id is not None:
            project = await self._projects.find_by_id(request.project_id)
            if project is None or project.manager_user_id != manager_user_id:
                raise AuthorizationError("You can only build teams for your own projects.")

        role_slots: list[TeamRoleSlot] = []
        for role in request.roles:
            skill = await self._skills.find_by_id(role.skill_id)
            if skill is None or not skill.is_active:
                raise SkillNotFoundError(f"Skill id {role.skill_id} not found or inactive.")
            role_slots.append(
                TeamRoleSlot(
                    role_title=role.role_title,
                    skill_id=role.skill_id,
                    skill_name=skill.name,
                    min_proficiency=role.min_proficiency,
                    utilization_percent=role.utilization_percent,
                )
            )

        team = await self._employees.find_by_manager(manager_user_id)
        member_pool: list[TeamMemberPool] = []
        for emp in team:
            if emp.id is None:
                continue
            emp_skills = await self._employees.find_skills(emp.id)
            skill_map = {s.skill_id: s.proficiency for s in emp_skills}
            active = await self._allocations.find_active_by_employee(emp.id)
            used = sum(a.utilization_percent for a in active)
            free = 100 - used
            allocated_until = max((a.to_date for a in active), default=None)
            member_pool.append(
                TeamMemberPool(
                    resource_profile_id=emp.id,
                    full_name=emp.full_name,
                    skills=skill_map,
                    free_percent=free,
                    allocated_until=allocated_until,
                )
            )

        outcome = match_team(role_slots, member_pool)
        role_responses: list[TeamRoleMatchResponse] = []
        gap_responses: list[TeamRoleGapResponse] = []

        for role_idx, role in enumerate(role_slots):
            if role_idx in outcome.assignments:
                member = member_pool[outcome.assignments[role_idx]]
                proficiency = member.skills[role.skill_id]
                role_responses.append(
                    TeamRoleMatchResponse(
                        role_title=role.role_title,
                        skill_id=role.skill_id,
                        skill_name=role.skill_name,
                        min_proficiency=role.min_proficiency.value,
                        filled=True,
                        resource_profile_id=member.resource_profile_id,
                        full_name=member.full_name,
                        proficiency=proficiency.value,
                        free_percent=member.free_percent,
                        reason=(
                            f"Best match: {proficiency.value} {role.skill_name}, "
                            f"{member.free_percent}% free capacity."
                        ),
                    )
                )
            else:
                reason = outcome.unfilled_reasons.get(role_idx)
                role_responses.append(
                    TeamRoleMatchResponse(
                        role_title=role.role_title,
                        skill_id=role.skill_id,
                        skill_name=role.skill_name,
                        min_proficiency=role.min_proficiency.value,
                        filled=False,
                        reason=reason,
                    )
                )

        for role_idx, gap_type, message, available_from in outcome.gaps:
            role = role_slots[role_idx]
            gap_responses.append(
                TeamRoleGapResponse(
                    role_title=role.role_title,
                    skill_id=role.skill_id,
                    skill_name=role.skill_name,
                    gap_type=gap_type,
                    message=message,
                    available_from=available_from,
                )
            )

        all_filled = all(r.filled for r in role_responses)
        input_summary = (audit_input or ", ".join(r.role_title for r in request.roles))[:500]
        response_summary = str(
            [{"role": r.role_title, "filled": r.filled, "name": r.full_name} for r in role_responses]
        )[:2000]

        await self._audit.save(
            AISuggestionAudit(
                id=None,
                request_type=AIRequestType.TEAM_BUILDER.value,
                subject_id=request.project_id or manager_user_id,
                input_summary=input_summary,
                response_summary=response_summary,
                provider=audit_provider or "deterministic",
                created_at=datetime.now(timezone.utc),
            )
        )

        return TeamBuilderResponse(
            roles=role_responses,
            gaps=gap_responses,
            all_roles_filled=all_filled,
        )
