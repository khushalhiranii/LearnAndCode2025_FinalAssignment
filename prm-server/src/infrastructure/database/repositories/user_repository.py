from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.enums import Role
from src.domain.ports.repositories import IUserRepository
from src.infrastructure.database.models.user_model import UserModel


class SQLAlchemyUserRepository(IUserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── private mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            full_name=model.full_name,
            email=model.email,
            username=model.username,
            password_hash=model.password_hash,
            role=Role(model.role),
            is_active=model.is_active,
            force_password_change=model.force_password_change,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        model = UserModel()
        if entity.id is not None:
            model.id = entity.id
        model.full_name = entity.full_name
        model.email = entity.email
        model.username = entity.username
        model.password_hash = entity.password_hash
        model.role = entity.role.value
        model.is_active = entity.is_active
        model.force_password_change = entity.force_password_change
        return model

    # ── IUserRepository implementation ───────────────────────────────────────

    async def find_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, user: User) -> User:
        model = self._to_model(user)
        self._session.add(model)
        await self._session.flush()  # populate auto-generated id
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_password(
        self,
        user_id: int,
        new_password_hash: str,
        force_password_change: bool,
    ) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                password_hash=new_password_hash,
                force_password_change=force_password_change,
            )
        )
