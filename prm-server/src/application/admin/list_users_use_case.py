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
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserListResponse:
        users, total = await self._users.find_all(
            role=role, is_active=is_active, page=page, page_size=page_size
        )
        return UserListResponse(
            items=[_to_response(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
        )


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,  # type: ignore[arg-type]
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        force_password_change=user.force_password_change,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
