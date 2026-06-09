from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.change_password_use_case import ChangePasswordUseCase
from src.application.auth.login_use_case import LoginUseCase
from src.application.dtos.auth_dtos import (
    ChangePasswordRequest,
    PasswordChangeRequiredResponse,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
)
from src.domain.exceptions import AuthorizationError
from src.infrastructure.database.engine import get_async_session
from src.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.security.jwt_handler import decode_temp_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _build_use_cases(session: AsyncSession) -> tuple[LoginUseCase, ChangePasswordUseCase]:
    repo = SQLAlchemyUserRepository(session)
    return LoginUseCase(repo), ChangePasswordUseCase(repo)


@router.post(
    "/login",
    response_model=LoginResponse | PasswordChangeRequiredResponse,
    status_code=200,
    summary="Authenticate user. Returns session token or password-change directive.",
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> LoginResponse | PasswordChangeRequiredResponse:
    login_uc, _ = _build_use_cases(session)
    return await login_uc.execute(request)


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=200,
    summary="Change password. Requires temp token issued by login when force_password_change=True.",
)
async def change_password(
    request: ChangePasswordRequest,
    authorization: str = Header(..., alias="Authorization"),
    session: AsyncSession = Depends(get_async_session),
) -> ChangePasswordResponse:
    if not authorization.startswith("Bearer "):
        raise AuthorizationError("Missing or malformed Authorization header.")
    token = authorization.removeprefix("Bearer ")
    user_id = decode_temp_token(token)  # validates that this is a temp token, not an access token
    _, change_uc = _build_use_cases(session)
    return await change_uc.execute(user_id, request)
