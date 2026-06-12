from datetime import datetime, timezone

from src.application.dtos.project_dtos import ProjectResponse, UpdateProjectRequest
from src.domain.entities.project import Project
from src.domain.enums import Role
from src.domain.exceptions import (
    DuplicateProjectNameError,
    InvalidProjectManagerError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from src.domain.ports.repositories import IProjectRepository, IUserRepository


class UpdateProjectUseCase:

    def __init__(
        self, project_repo: IProjectRepository, user_repo: IUserRepository
    ) -> None:
        self._projects = project_repo
        self._users = user_repo

    async def execute(self, project_id: int, request: UpdateProjectRequest) -> ProjectResponse:
        project = await self._projects.find_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found.")

        # Name uniqueness check (only if name is changing)
        if request.name is not None and request.name != project.name:
            existing = await self._projects.find_by_name(request.name)
            if existing is not None:
                raise DuplicateProjectNameError(
                    f"A project named '{request.name}' already exists."
                )

        # Validate new manager if provided
        if request.manager_user_id is not None:
            manager = await self._users.find_by_id(request.manager_user_id)
            if manager is None:
                raise UserNotFoundError(
                    f"User {request.manager_user_id} not found."
                )
            manager_role = await self._users.find_active_role(request.manager_user_id)
            if manager_role != Role.MANAGER:
                raise InvalidProjectManagerError(
                    f"User {manager.username} does not have the MANAGER role."
                )
            if not manager.is_account_enabled:
                raise InvalidProjectManagerError(
                    f"Manager {manager.username} is inactive."
                )

        # Apply partial updates
        updated = Project(
            id=project.id,
            name=request.name if request.name is not None else project.name,
            description=request.description if request.description is not None else project.description,
            manager_user_id=request.manager_user_id if request.manager_user_id is not None else project.manager_user_id,
            status=request.status if request.status is not None else project.status,
            total_story_points=request.total_story_points if request.total_story_points is not None else project.total_story_points,
            completed_story_points=project.completed_story_points,  # never touched here
            start_date=request.start_date if request.start_date is not None else project.start_date,
            end_date=request.end_date if request.end_date is not None else project.end_date,
            created_at=project.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        saved = await self._projects.save(updated)
        return _to_response(saved)


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
