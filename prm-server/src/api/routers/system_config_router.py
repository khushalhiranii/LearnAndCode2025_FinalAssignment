from fastapi import APIRouter, Depends

from src.api.dependencies import require_admin
from src.application.admin.system_config_use_case import SystemConfigUseCase
from src.application.dtos.system_config_dtos import SystemConfigResponse, UpdateSystemConfigRequest
from src.domain.entities.user import User
from src.infrastructure.scheduler.scheduler_runner import get_scheduler
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/admin/config", tags=["admin-system-config"])


@router.get("", response_model=dict)
async def get_system_config(
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SystemConfigUseCase(uow.system_config)
    result = await use_case.get_config()
    return {"success": True, "data": result.model_dump()}


@router.patch("", response_model=dict)
async def update_system_config(
    request: UpdateSystemConfigRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SystemConfigUseCase(uow.system_config)
    result = await use_case.update_config(request)
    if request.scheduler_interval_minutes is not None or request.scheduler_interval_hours is not None:
        get_scheduler().reschedule(result.scheduler_interval_minutes)
    return {"success": True, "data": result.model_dump()}
