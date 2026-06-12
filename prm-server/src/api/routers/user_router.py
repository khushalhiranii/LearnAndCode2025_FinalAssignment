from fastapi import APIRouter, Depends, Query

from src.api.dependencies import require_admin
from src.application.admin.create_user_use_case import CreateUserUseCase
from src.application.admin.deactivate_user_use_case import DeactivateUserUseCase
from src.application.admin.list_users_use_case import ListUsersUseCase
from src.application.admin.reactivate_user_use_case import ReactivateUserUseCase
from src.application.admin.reset_password_use_case import ResetPasswordUseCase
from src.application.dtos.user_dtos import (
    CreateUserRequest,
    ResetPasswordResponse,
    UserListResponse,
    UserResponse,
)
from src.domain.entities.user import User
from src.domain.enums import Role
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.post("", response_model=dict, status_code=201)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = CreateUserUseCase(uow.users, uow.employees)
    user_response, temp_password = await use_case.execute(request)
    return {
        "success": True,
        "data": {**user_response.model_dump(), "temp_password": temp_password},
    }


@router.get("", response_model=dict)
async def list_users(
    role: Role | None = Query(None),
    is_account_enabled: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = ListUsersUseCase(uow.users)
    result = await use_case.execute(role=role, is_account_enabled=is_account_enabled, page=page, page_size=page_size)
    return {"success": True, "data": result.model_dump()}


@router.post("/{user_id}/deactivate", response_model=dict)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = DeactivateUserUseCase(uow.users, uow.employees)
    result = await use_case.execute(user_id, acting_admin_id=current_user.id)  # type: ignore[arg-type]
    return {"success": True, "data": result.model_dump()}


@router.post("/{user_id}/reactivate", response_model=dict)
async def reactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = ReactivateUserUseCase(uow.users, uow.employees)
    result = await use_case.execute(user_id)
    return {"success": True, "data": result.model_dump()}


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_password(
    user_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = ResetPasswordUseCase(uow.users)
    result = await use_case.execute(user_id)
    return {"success": True, "data": result.model_dump()}
