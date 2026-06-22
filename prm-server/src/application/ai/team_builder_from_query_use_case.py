from src.application.ai.team_builder_use_case import TeamBuilderUseCase
from src.application.ai.team_query_parser import parse_team_query_rule_based
from src.application.dtos.ai_dtos import (
    ParsedTeamRoleResponse,
    TeamBuilderFromQueryRequest,
    TeamBuilderFromQueryResponse,
    TeamBuilderRequest,
    TeamRoleRequest,
)
from src.domain.enums import ProficiencyLevel
from src.domain.exceptions import TeamQueryParseError
from src.domain.ports.ai_provider import IAIProvider, SkillCatalogEntry
from src.domain.ports.repositories import ISkillRepository


class TeamBuilderFromQueryUseCase:

    def __init__(
        self,
        team_builder: TeamBuilderUseCase,
        skills: ISkillRepository,
        ai_provider: IAIProvider,
    ) -> None:
        self._team_builder = team_builder
        self._skills = skills
        self._ai = ai_provider

    async def execute(
        self, manager_user_id: int, request: TeamBuilderFromQueryRequest
    ) -> TeamBuilderFromQueryResponse:
        catalog = await self._load_catalog()
        if not catalog:
            raise TeamQueryParseError(
                "No skills in the catalog. Ask admin to add skills before building a team."
            )

        ai_parsed = True
        parsed = []
        try:
            parsed = await self._ai.parse_team_requirements(request.query, catalog)
        except Exception:
            ai_parsed = False
            parsed = []

        if not parsed:
            parsed = parse_team_query_rule_based(request.query, catalog)
            ai_parsed = False

        if not parsed:
            raise TeamQueryParseError(
                "Could not identify team roles from your description. "
                "Try naming each role and skill clearly, e.g. "
                "'needing a Senior Java Developer, a DevOps Engineer and a QA tester'."
            )

        skill_names = {s.skill_id: s.name for s in catalog}
        team_roles = [
            TeamRoleRequest(
                role_title=p.role_title,
                skill_id=p.skill_id,
                min_proficiency=ProficiencyLevel(p.min_proficiency),
                utilization_percent=p.utilization_percent,
            )
            for p in parsed
        ]

        provider_label = self._ai.provider_name if ai_parsed else "rule-based"
        result = await self._team_builder.execute(
            manager_user_id,
            TeamBuilderRequest(roles=team_roles, project_id=request.project_id),
            audit_input=request.query[:500],
            audit_provider=f"{provider_label}+deterministic",
        )

        parsed_responses = [
            ParsedTeamRoleResponse(
                role_title=p.role_title,
                skill_id=p.skill_id,
                skill_name=skill_names.get(p.skill_id, ""),
                min_proficiency=p.min_proficiency,
                utilization_percent=p.utilization_percent,
            )
            for p in parsed
        ]

        return TeamBuilderFromQueryResponse(
            query=request.query,
            parsed_roles=parsed_responses,
            ai_parsed=ai_parsed,
            roles=result.roles,
            gaps=result.gaps,
            all_roles_filled=result.all_roles_filled,
            note=result.note,
        )

    async def _load_catalog(self) -> list[SkillCatalogEntry]:
        skills = await self._skills.find_all()
        return [
            SkillCatalogEntry(skill_id=s.id, name=s.name, category=s.category)
            for s in skills
            if s.is_active and s.id is not None
        ]
