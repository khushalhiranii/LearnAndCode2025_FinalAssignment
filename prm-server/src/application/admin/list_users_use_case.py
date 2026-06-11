from src.application.dtos.user_dtos import UserListResponse, UserResponse
from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.ports.repositories import IUserRepository


class ListUsersUseCase:

    def __init__(self, user_repo: IUserRepository) -> None:
        self._users = user_repo

    async def execute(
        self,
        role: Role | None = None,
        is_account_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserListResponse:
        users, total = await self._users.find_all(
            role=role, is_account_enabled=is_account_enabled, page=page, page_size=page_size
        )
        # Load active role for each user (acceptable for list sizes typical in admin UIs)
        items = []
        for u in users:
            active_role = await self._users.find_active_role(u.id)  # type: ignore[arg-type]
            items.append(_to_response(u, active_role))
        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


def _to_response(user: User, role: Role | None) -> UserResponse:
    return UserResponse(
        id=user.id,  # type: ignore[arg-type]
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=role,
        is_account_enabled=user.is_account_enabled,
        force_password_change=user.force_password_change,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
