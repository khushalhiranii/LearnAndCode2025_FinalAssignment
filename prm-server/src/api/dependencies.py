from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.exceptions import AuthorizationError
from src.infrastructure.database.engine import get_async_session
from src.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.security.jwt_handler import decode_access_token


async def get_user_repository(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserRepository, None]:
    yield SQLAlchemyUserRepository(session)


def _role_from_header(authorization: str) -> str:
    if not authorization.startswith("Bearer "):
        raise AuthorizationError("Missing or malformed Authorization header.")
    payload = decode_access_token(authorization.removeprefix("Bearer "))
    return payload.get("role", "")


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> User:
    if not authorization.startswith("Bearer "):
        raise AuthorizationError("Missing or malformed Authorization header.")
    token = authorization.removeprefix("Bearer ")
    payload = decode_access_token(token)
    user_id = int(payload["sub"])
    user = await user_repo.find_by_id(user_id)
    if user is None or not user.is_account_enabled:
        raise AuthorizationError("User account not found or inactive.")
    return user


def _require_role(role: Role):
    async def _dependency(
        authorization: str = Header(..., alias="Authorization"),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if _role_from_header(authorization) != role.value:
            raise AuthorizationError(f"{role.value.capitalize()} role required.")
        return current_user
    return _dependency


require_admin = _require_role(Role.ADMIN)
require_manager = _require_role(Role.MANAGER)
require_employee = _require_role(Role.EMPLOYEE)
