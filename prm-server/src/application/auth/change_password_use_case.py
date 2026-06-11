from src.application.dtos.auth_dtos import ChangePasswordRequest, ChangePasswordResponse
from src.domain.exceptions import UserNotFoundError
from src.domain.ports.repositories import IUserRepository
from src.infrastructure.security.jwt_handler import create_access_token
from src.infrastructure.security.password_hasher import hash_password


class ChangePasswordUseCase:
    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo

    async def execute(
        self, user_id: int, request: ChangePasswordRequest
    ) -> ChangePasswordResponse:
        # Pydantic already validated strength and matching in ChangePasswordRequest
        user = await self._user_repo.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found.")

        new_hash = hash_password(request.new_password)
        await self._user_repo.update_password(
            user_id=user_id,
            new_password_hash=new_hash,
            force_password_change=False,
        )

        # Re-fetch to get updated state for the token
        updated_user = await self._user_repo.find_by_id(user_id)
        if updated_user is None:
            raise UserNotFoundError(f"User {user_id} not found after update.")

        role = await self._user_repo.find_active_role(user_id)  # type: ignore[arg-type]
        if role is None:
            from src.domain.exceptions import InactiveUserError
            raise InactiveUserError("No active role assigned to this account.")

        access_token = create_access_token(updated_user.id, role.value)  # type: ignore[arg-type]
        return ChangePasswordResponse(
            access_token=access_token,
            role=role.value,
            full_name=updated_user.full_name,
        )
