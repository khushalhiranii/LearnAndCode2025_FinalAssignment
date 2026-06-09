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

    async def find_all(
        self,
        role: "Role | None" = None,
        is_active: "bool | None" = None,
        page: int = 1,
        page_size: int = 20,
    ) -> "tuple[list[User], int]":
        from sqlalchemy import func

        q = select(UserModel)
        if role is not None:
            q = q.where(UserModel.role == role.value)
        if is_active is not None:
            q = q.where(UserModel.is_active == is_active)

        count_result = await self._session.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count_result.scalar_one()

        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(q)).scalars().all()
        return [self._to_entity(m) for m in rows], total

    async def find_by_email(self, email: str) -> "User | None":
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_active(self, user_id: int, is_active: bool) -> None:
        from datetime import datetime, timezone
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=is_active, updated_at=datetime.now(timezone.utc))
        )
