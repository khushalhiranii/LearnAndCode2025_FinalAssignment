from datetime import datetime, timezone

from src.application.dtos.project_dtos import CreateProjectRequest, ProjectResponse
from src.domain.entities.project import Project
from src.domain.enums import Role
from src.domain.exceptions import (
    DuplicateProjectNameError,
    InvalidProjectManagerError,
    UserNotFoundError,
)
from src.domain.ports.repositories import IProjectRepository, IUserRepository


class CreateProjectUseCase:

    def __init__(
        self, project_repo: IProjectRepository, user_repo: IUserRepository
    ) -> None:
        self._projects = project_repo
        self._users = user_repo

    async def execute(self, request: CreateProjectRequest) -> ProjectResponse:
        # 1. Name uniqueness
        existing = await self._projects.find_by_name(request.name)
        if existing is not None:
            raise DuplicateProjectNameError(
                f"A project named '{request.name}' already exists."
            )

        # 2. Manager must exist
        manager = await self._users.find_by_id(request.manager_user_id)
        if manager is None:
            raise UserNotFoundError(
                f"User {request.manager_user_id} not found."
            )

        # 3. Manager must have MANAGER role
        manager_role = await self._users.find_active_role(request.manager_user_id)
        if manager_role != Role.MANAGER:
            raise InvalidProjectManagerError(
                f"User {manager.username} does not have the MANAGER role."
            )

        # 4. Manager must be active
        if not manager.is_account_enabled:
            raise InvalidProjectManagerError(
                f"Manager {manager.username} is inactive."
            )

        now = datetime.now(timezone.utc)
        project = Project(
            id=None,
            name=request.name,
            description=request.description,
            manager_user_id=request.manager_user_id,
            status=request.status,
            total_story_points=request.total_story_points,
            completed_story_points=0,
            start_date=request.start_date,
            end_date=request.end_date,
            created_at=now,
            updated_at=now,
        )
        saved = await self._projects.save(project)
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
