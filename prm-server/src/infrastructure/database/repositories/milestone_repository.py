from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.milestone import Milestone
from src.domain.enums import MilestoneStatus
from src.domain.ports.repositories import IMilestoneRepository
from src.infrastructure.database.models.milestone_model import MilestoneModel


class SQLAlchemyMilestoneRepository(IMilestoneRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: MilestoneModel) -> Milestone:
        return Milestone(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description,
            due_date=model.due_date,
            status=MilestoneStatus(model.status),
            story_points=model.story_points,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def find_by_id(self, milestone_id: int) -> Milestone | None:
        result = await self._session.execute(
            select(MilestoneModel).where(MilestoneModel.id == milestone_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_project(self, project_id: int) -> list[Milestone]:
        result = await self._session.execute(
            select(MilestoneModel)
            .where(MilestoneModel.project_id == project_id)
            .order_by(MilestoneModel.due_date.asc().nulls_last())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, milestone: Milestone) -> Milestone:
        model = MilestoneModel()
        if milestone.id is not None:
            model.id = milestone.id
        model.project_id = milestone.project_id
        model.title = milestone.title
        model.description = milestone.description
        model.due_date = milestone.due_date
        model.status = milestone.status.value
        model.story_points = milestone.story_points
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_status(
        self, milestone_id: int, status: MilestoneStatus
    ) -> None:
        await self._session.execute(
            update(MilestoneModel)
            .where(MilestoneModel.id == milestone_id)
            .values(status=status.value, updated_at=datetime.now(timezone.utc))
        )

    async def sum_done_story_points(self, project_id: int) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.sum(MilestoneModel.story_points), 0)).where(
                MilestoneModel.project_id == project_id,
                MilestoneModel.status == MilestoneStatus.DONE.value,
            )
        )
        return result.scalar_one()
