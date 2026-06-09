from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.project import Project
from src.domain.enums import ProjectStatus
from src.domain.ports.repositories import IProjectRepository
from src.infrastructure.database.models.project_model import ProjectModel


class SQLAlchemyProjectRepository(IProjectRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── private mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            manager_user_id=model.manager_user_id,
            status=ProjectStatus(model.status),
            total_story_points=model.total_story_points,
            completed_story_points=model.completed_story_points,
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ── IProjectRepository ───────────────────────────────────────────────────

    async def find_by_id(self, project_id: int) -> Project | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all(
        self,
        status: ProjectStatus | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Project], int]:
        q = select(ProjectModel)
        if status is not None:
            q = q.where(ProjectModel.status == status.value)
        if manager_user_id is not None:
            q = q.where(ProjectModel.manager_user_id == manager_user_id)

        count_result = await self._session.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count_result.scalar_one()

        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(q)).scalars().all()
        return [self._to_entity(m) for m in rows], total

    async def find_by_name(self, name: str) -> Project | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, project: Project) -> Project:
        if project.id is not None:
            result = await self._session.execute(
                select(ProjectModel).where(ProjectModel.id == project.id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                model = ProjectModel()
                model.id = project.id
        else:
            model = ProjectModel()

        model.name = project.name
        model.description = project.description
        model.manager_user_id = project.manager_user_id
        model.status = project.status.value
        model.total_story_points = project.total_story_points
        model.completed_story_points = project.completed_story_points
        model.start_date = project.start_date
        model.end_date = project.end_date

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_status(self, project_id: int, status: ProjectStatus) -> None:
        await self._session.execute(
            update(ProjectModel)
            .where(ProjectModel.id == project_id)
            .values(status=status.value, updated_at=datetime.now(timezone.utc))
        )

    async def update_completed_points(self, project_id: int, points: int) -> None:
        await self._session.execute(
            update(ProjectModel)
            .where(ProjectModel.id == project_id)
            .values(
                completed_story_points=points,
                updated_at=datetime.now(timezone.utc),
            )
        )
