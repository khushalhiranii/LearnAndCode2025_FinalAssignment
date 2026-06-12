"""AI endpoints for managers."""

from fastapi import APIRouter, Depends

from src.api.dependencies import require_manager
from src.application.ai.risk_summary_use_case import RiskSummaryUseCase
from src.application.ai.skill_match_use_case import SkillMatchUseCase
from src.application.dtos.ai_dtos import (
    RiskSummaryRequest,
    RiskSummaryResponse,
    SkillMatchRequest,
    SkillMatchResponse,
)
from src.domain.entities.user import User
from src.infrastructure.llm.ai_provider_factory import AIProviderFactory
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/manager/ai", tags=["manager-ai"])


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
