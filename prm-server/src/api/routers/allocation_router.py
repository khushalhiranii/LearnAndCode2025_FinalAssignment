from fastapi import APIRouter, Depends, status

from src.api.dependencies import require_manager
from src.application.dtos.allocation_dtos import (
    AllocateEmployeeRequest,
    AllocationResponse,
    EndAllocationRequest,
    ResourceDashboardResponse,
)
from src.application.manager.allocation_use_case import AllocationUseCase, _to_allocation_response
from src.domain.entities.user import User
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/manager", tags=["manager-allocations"])


@router.get("/dashboard", response_model=ResourceDashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ResourceDashboardResponse:
    use_case = AllocationUseCase(uow.allocations, uow.employees, uow.projects)
    return await use_case.get_dashboard(current_user.id)


@router.post(
    "/allocations",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def allocate_employee(
    request: AllocateEmployeeRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> AllocationResponse:
    use_case = AllocationUseCase(uow.allocations, uow.employees, uow.projects)
    return await use_case.allocate(current_user.id, request)


@router.get("/allocations", response_model=list[AllocationResponse])
async def list_my_allocations(
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[AllocationResponse]:
    """List all allocations (active + ended) across the manager's team."""
    employees = await uow.employees.find_by_manager(current_user.id)
    results = []
    for emp in employees:
        emp_allocs = await uow.allocations.find_by_employee(emp.id)
        results.extend(emp_allocs)
    return [_to_allocation_response(a) for a in results]


@router.patch(
    "/allocations/{allocation_id}/end",
    response_model=AllocationResponse,
)
async def end_allocation(
    allocation_id: int,
    request: EndAllocationRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> AllocationResponse:
    use_case = AllocationUseCase(uow.allocations, uow.employees, uow.projects)
    return await use_case.end_allocation(current_user.id, allocation_id, request)


@router.get("/projects", response_model=list[dict])
async def list_my_projects(
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[dict]:
    """Return projects managed by the current user (all statuses)."""
    projects_result, _ = await uow.projects.find_all(
        manager_user_id=current_user.id, page=1, page_size=100
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status.value,
            "total_story_points": p.total_story_points,
            "completed_story_points": p.completed_story_points,
        }
        for p in projects_result
    ]
