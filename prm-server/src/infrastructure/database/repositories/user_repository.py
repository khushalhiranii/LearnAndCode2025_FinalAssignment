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
            is_account_enabled=model.is_account_enabled,
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
        model.is_account_enabled = entity.is_account_enabled
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
        await self._session.flush()
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
        is_account_enabled: "bool | None" = None,
        page: int = 1,
        page_size: int = 20,
    ) -> "tuple[list[User], int]":
        from sqlalchemy import func
        from src.infrastructure.database.models.role_model import RoleModel, UserRoleModel

        q = select(UserModel)
        if role is not None:
            # join user_roles to filter by role name
            q = (
                q.join(UserRoleModel, UserRoleModel.user_id == UserModel.id)
                .join(RoleModel, RoleModel.id == UserRoleModel.role_id)
                .where(RoleModel.name == role.value)
                .where(UserRoleModel.to_date.is_(None))
            )
        if is_account_enabled is not None:
            q = q.where(UserModel.is_account_enabled == is_account_enabled)

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

    async def update_active(self, user_id: int, is_account_enabled: bool) -> None:
        from datetime import datetime, timezone
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_account_enabled=is_account_enabled, updated_at=datetime.now(timezone.utc))
        )

    async def find_active_role(self, user_id: int) -> "Role | None":
        """Return the currently active Role for user_id from user_roles (to_date IS NULL)."""
        from src.infrastructure.database.models.role_model import RoleModel, UserRoleModel

        result = await self._session.execute(
            select(RoleModel.name)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(UserRoleModel.user_id == user_id)
            .where(UserRoleModel.to_date.is_(None))
        )
        role_name = result.scalar_one_or_none()
        return Role(role_name) if role_name else None

    async def assign_role(
        self,
        user_id: int,
        role: "Role",
        from_date,
        granted_by_user_id: "int | None",
        reason: "str | None",
    ) -> None:
        """Close any current active user_roles row then insert new one."""
        from datetime import date as _date
        from src.infrastructure.database.models.role_model import RoleModel, UserRoleModel

        # Close existing active role
        await self._session.execute(
            update(UserRoleModel)
            .where(UserRoleModel.user_id == user_id)
            .where(UserRoleModel.to_date.is_(None))
            .values(to_date=from_date)
        )

        role_result = await self._session.execute(
            select(RoleModel).where(RoleModel.name == role.value)
        )
        role_model = role_result.scalar_one()

        new_row = UserRoleModel()
        new_row.user_id = user_id
        new_row.role_id = role_model.id
        new_row.from_date = from_date
        new_row.to_date = None
        new_row.granted_by_user_id = granted_by_user_id
        new_row.reason = reason
        self._session.add(new_row)

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
