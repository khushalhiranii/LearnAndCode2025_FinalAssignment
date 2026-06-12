from src.application.dtos.project_dtos import ProjectListResponse, ProjectResponse
from src.domain.entities.project import Project
from src.domain.enums import ProjectStatus
from src.domain.ports.repositories import IProjectRepository


class ListProjectsUseCase:

    def __init__(self, project_repo: IProjectRepository) -> None:
        self._projects = project_repo

    async def execute(
        self,
        status: ProjectStatus | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProjectListResponse:
        items, total = await self._projects.find_all(
            status=status,
            manager_user_id=manager_user_id,
            page=page,
            page_size=page_size,
        )
        return ProjectListResponse(
            items=[_to_response(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        manager_user_id=project.manager_user_id,
        status=project.status,
        total_story_points=project.total_story_points,
        completed_story_points=project.completed_story_points,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
