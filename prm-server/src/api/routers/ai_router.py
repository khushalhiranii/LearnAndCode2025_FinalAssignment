"""AI endpoints for managers."""

from fastapi import APIRouter, Depends

from src.api.dependencies import require_manager
from src.application.ai.risk_summary_use_case import RiskSummaryUseCase
from src.application.ai.skill_match_use_case import SkillMatchUseCase
from src.application.ai.team_builder_from_query_use_case import TeamBuilderFromQueryUseCase
from src.application.ai.team_builder_use_case import TeamBuilderUseCase
from src.application.dtos.ai_dtos import (
    RiskSummaryRequest,
    RiskSummaryResponse,
    SkillMatchRequest,
    SkillMatchResponse,
    TeamBuilderFromQueryRequest,
    TeamBuilderFromQueryResponse,
    TeamBuilderRequest,
    TeamBuilderResponse,
)
from src.domain.entities.user import User
from src.infrastructure.llm.ai_provider_factory import AIProviderFactory
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/manager/ai", tags=["manager-ai"])


@router.get(
    "/skills",
    summary="List skills for team builder",
    description="Active skills from the catalog for defining team roles.",
)
async def list_skills_for_team_builder(
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[dict[str, int | str]]:
    _ = current_user
    skills = await uow.skills.find_all()
    return [
        {"id": s.id, "name": s.name, "category": s.category}
        for s in skills
        if s.is_active and s.id is not None
    ]


@router.post(
    "/skill-match",
    response_model=SkillMatchResponse,
    summary="AI skill matcher",
    description="Natural language search for team resources with ranked suggestions.",
)
async def skill_match(
    request: SkillMatchRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> SkillMatchResponse:
    config = await uow.system_config.get_config()
    provider = AIProviderFactory.create(config)
    use_case = SkillMatchUseCase(
        uow.employees,
        uow.allocations,
        uow.timesheets,
        uow.users,
        uow.projects,
        provider,
        uow.ai_audit,
    )
    return await use_case.execute(current_user.id, request)  # type: ignore[arg-type]


@router.post(
    "/risk-summary",
    response_model=RiskSummaryResponse,
    summary="AI project risk summary",
    description="Plain-English risk summary from milestone and timesheet data.",
)
async def risk_summary(
    request: RiskSummaryRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> RiskSummaryResponse:
    config = await uow.system_config.get_config()
    provider = AIProviderFactory.create(config)
    use_case = RiskSummaryUseCase(
        uow.projects,
        uow.milestones,
        uow.allocations,
        uow.timesheets,
        uow.project_health,
        provider,
        uow.ai_audit,
    )
    return await use_case.execute(current_user.id, request)  # type: ignore[arg-type]


@router.post(
    "/team-builder",
    response_model=TeamBuilderResponse,
    summary="Team builder with skill match",
    description=(
        "Define a whole project team at once and get the best available "
        "match for every role in a single pass."
    ),
)
async def team_builder(
    request: TeamBuilderRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TeamBuilderResponse:
    use_case = TeamBuilderUseCase(
        uow.employees,
        uow.allocations,
        uow.skills,
        uow.projects,
        uow.ai_audit,
    )
    return await use_case.execute(current_user.id, request)  # type: ignore[arg-type]


@router.post(
    "/team-builder-from-query",
    response_model=TeamBuilderFromQueryResponse,
    summary="Team builder from natural language",
    description=(
        "Describe a whole project team in plain English and get the best "
        "available match for every role in a single pass."
    ),
)
async def team_builder_from_query(
    request: TeamBuilderFromQueryRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TeamBuilderFromQueryResponse:
    config = await uow.system_config.get_config()
    provider = AIProviderFactory.create(config)
    team_builder = TeamBuilderUseCase(
        uow.employees,
        uow.allocations,
        uow.skills,
        uow.projects,
        uow.ai_audit,
    )
    use_case = TeamBuilderFromQueryUseCase(team_builder, uow.skills, provider)
    return await use_case.execute(current_user.id, request)  # type: ignore[arg-type]
