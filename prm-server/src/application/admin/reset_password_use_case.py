import secrets
import string

from src.application.dtos.user_dtos import ResetPasswordResponse
from src.domain.exceptions import UserNotFoundError
from src.domain.ports.repositories import IUserRepository
from src.infrastructure.security.password_hasher import hash_password

_TEMP_PWD_ALPHABET = string.ascii_letters + string.digits + "!@#$%"
_TEMP_PWD_LENGTH = 12


def _generate_temp_password() -> str:
    return "".join(secrets.choice(_TEMP_PWD_ALPHABET) for _ in range(_TEMP_PWD_LENGTH))


class ResetPasswordUseCase:

    def __init__(self, user_repo: IUserRepository) -> None:
        self._users = user_repo

    async def execute(self, target_user_id: int) -> ResetPasswordResponse:
        user = await self._users.find_by_id(target_user_id)
        if user is None:
            raise UserNotFoundError(f"User {target_user_id} not found.")

        temp_password = _generate_temp_password()
        await self._users.update_password(
            user_id=target_user_id,
            new_password_hash=hash_password(temp_password),
            force_password_change=True,
        )

        return ResetPasswordResponse(temp_password=temp_password)
