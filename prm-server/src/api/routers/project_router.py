from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import require_admin
from src.application.admin.create_project_use_case import CreateProjectUseCase
from src.application.admin.list_projects_use_case import ListProjectsUseCase
from src.application.admin.milestone_use_case import MilestoneUseCase
from src.application.admin.update_project_use_case import UpdateProjectUseCase
from src.application.dtos.project_dtos import (
    AddMilestoneRequest,
    CreateProjectRequest,
    MilestoneResponse,
    ProjectListResponse,
    ProjectResponse,
    UpdateMilestoneStatusRequest,
    UpdateProjectRequest,
)
from src.domain.entities.user import User
from src.domain.enums import ProjectStatus
from src.domain.exceptions import ProjectNotFoundError
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/admin", tags=["admin-projects"])


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    status: ProjectStatus | None = Query(default=None),
    manager_user_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProjectListResponse:
    use_case = ListProjectsUseCase(uow.projects)
    return await use_case.execute(
        status=status,
        manager_user_id=manager_user_id,
        page=page,
        page_size=page_size,
    )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProjectResponse:
    use_case = CreateProjectUseCase(uow.projects, uow.users)
    return await use_case.execute(request)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProjectResponse:
    project = await uow.projects.find_by_id(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project {project_id} not found.")
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


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    request: UpdateProjectRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProjectResponse:
    use_case = UpdateProjectUseCase(uow.projects, uow.users)
    return await use_case.execute(project_id, request)


@router.get("/projects/{project_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(
    project_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[MilestoneResponse]:
    use_case = MilestoneUseCase(uow.projects, uow.milestones)
    return await use_case.list_milestones(project_id)


@router.post(
    "/projects/{project_id}/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_milestone(
    project_id: int,
    request: AddMilestoneRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> MilestoneResponse:
    use_case = MilestoneUseCase(uow.projects, uow.milestones)
    return await use_case.add_milestone(project_id, request)


@router.patch(
    "/projects/{project_id}/milestones/{milestone_id}/status",
    response_model=MilestoneResponse,
)
async def update_milestone_status(
    project_id: int,
    milestone_id: int,
    request: UpdateMilestoneStatusRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> MilestoneResponse:
    use_case = MilestoneUseCase(uow.projects, uow.milestones)
    return await use_case.update_milestone_status(milestone_id, request)
