from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import require_manager
from src.application.admin.list_projects_use_case import ListProjectsUseCase
from src.application.dtos.ai_dtos import ProjectHealthResponse
from src.application.dtos.project_dtos import ProjectListResponse, ProjectResponse
from src.domain.entities.user import User
from src.domain.exceptions import AuthorizationError, ProjectNotFoundError
from src.infrastructure.database.repositories.project_health_repository import parse_risk_flags
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(tags=["manager-projects"])


@router.get(
    "/manager/projects",
    response_model=ProjectListResponse,
    summary="List manager projects",
    description="Paginated projects owned by the logged-in manager, with latest health status.",
)
async def list_manager_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProjectListResponse:
    use_case = ListProjectsUseCase(uow.projects)
    result = await use_case.execute(
        manager_user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    project_ids = [p.id for p in result.items]
    health_map = await uow.project_health.find_latest_by_projects(project_ids)
    enriched = []
    for p in result.items:
        data = p.model_dump()
        snap = health_map.get(p.id)
        data["health_status"] = snap.health_status.value if snap else "ON_TRACK"
        enriched.append(ProjectResponse(**data))
    return ProjectListResponse(
        items=enriched,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/manager/projects/{project_id}",
    summary="Project detail with milestones",
    description="Full project detail including milestones and allocated resources.",
)
async def get_manager_project_detail(
    project_id: int,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    project = await uow.projects.find_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.manager_user_id != current_user.id:
        raise AuthorizationError("You can only view your own projects.")

    milestones = await uow.milestones.find_by_project(project_id)
    allocations = await uow.allocations.find_by_project(project_id, active_only=True)
    snap = await uow.project_health.find_latest_by_project(project_id)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "total_story_points": project.total_story_points,
        "completed_story_points": project.completed_story_points,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "health_status": snap.health_status.value if snap else "ON_TRACK",
        "risk_flags": parse_risk_flags(snap.risk_flags_json) if snap else [],
        "milestones": [
            {
                "id": m.id,
                "title": m.title,
                "due_date": m.due_date,
                "status": m.status.value,
                "story_points": m.story_points,
            }
            for m in milestones
        ],
        "allocations": [
            {
                "resource_profile_id": a.resource_profile_id,
                "utilization_percent": a.utilization_percent,
                "from_date": a.from_date,
                "to_date": a.to_date,
            }
            for a in allocations
        ],
    }


@router.get(
    "/manager/projects/{project_id}/health",
    response_model=ProjectHealthResponse,
    summary="Latest project health snapshot",
)
async def get_project_health(
    project_id: int,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProjectHealthResponse:
    project = await uow.projects.find_by_id(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project {project_id} not found.")
    if project.manager_user_id != current_user.id:
        raise AuthorizationError("You can only view health for your own projects.")
    snap = await uow.project_health.find_latest_by_project(project_id)
    if snap is None:
        return ProjectHealthResponse(
            project_id=project_id,
            health_status="ON_TRACK",
            risk_flags=[],
            computed_at=None,
        )
    return ProjectHealthResponse(
        project_id=project_id,
        health_status=snap.health_status.value,
        risk_flags=parse_risk_flags(snap.risk_flags_json),
        computed_at=snap.computed_at,
    )
