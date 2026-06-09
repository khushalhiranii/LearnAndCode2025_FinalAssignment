from src.application.dtos.auth_dtos import (
    PasswordChangeRequiredResponse,
    LoginRequest,
    LoginResponse,
)
from src.domain.exceptions import InactiveUserError, InvalidCredentialsError
from src.domain.ports.repositories import IUserRepository
from src.infrastructure.security.jwt_handler import create_access_token, create_temp_token
from src.infrastructure.security.password_hasher import verify_password


class LoginUseCase:
    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo

    async def execute(
        self, request: LoginRequest
    ) -> LoginResponse | PasswordChangeRequiredResponse:
        user = await self._user_repo.find_by_username(request.username)

        if user is None:
            raise InvalidCredentialsError("Invalid username or password.")

        if not verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password.")

        if not user.is_active:
            raise InactiveUserError("This account has been deactivated.")

        if user.force_password_change:
            temp_token = create_temp_token(user.id)  # type: ignore[arg-type]
            return PasswordChangeRequiredResponse(temp_token=temp_token)

        access_token = create_access_token(user.id, user.role)  # type: ignore[arg-type]
        return LoginResponse(
            access_token=access_token,
            role=user.role.value,
            full_name=user.full_name,
        )
