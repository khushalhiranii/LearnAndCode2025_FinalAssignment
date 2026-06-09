from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.skill import Skill
from src.domain.ports.repositories import ISkillRepository
from src.infrastructure.database.models.skill_model import SkillModel


class SQLAlchemySkillRepository(ISkillRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: SkillModel) -> Skill:
        return Skill(
            id=model.id,
            name=model.name,
            category=model.category,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def find_by_id(self, skill_id: int) -> Skill | None:
        result = await self._session.execute(
            select(SkillModel).where(SkillModel.id == skill_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all(self) -> list[Skill]:
        result = await self._session.execute(
            select(SkillModel).order_by(SkillModel.name)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_name(self, name: str) -> Skill | None:
        result = await self._session.execute(
            select(SkillModel).where(SkillModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, skill: Skill) -> Skill:
        model = SkillModel()
        if skill.id is not None:
            model.id = skill.id
        model.name = skill.name
        model.category = skill.category
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)
