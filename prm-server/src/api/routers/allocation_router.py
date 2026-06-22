from fastapi import APIRouter, Depends, status

from src.api.dependencies import require_admin, require_manager
from src.application.dtos.allocation_dtos import (
    AllocateEmployeeRequest,
    AllocationResponse,
    EndAllocationRequest,
    ResourceDashboardResponse,
)
from src.application.manager.allocation_use_case import AllocationUseCase, _to_allocation_response
from src.application.manager.restore_timesheet_access_use_case import RestoreTimesheetAccessUseCase
from src.application.notifications.email_notification_service import EmailNotificationService
from src.infrastructure.email.email_provider_factory import EmailProviderFactory
from src.domain.entities.user import User
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(tags=["allocations"])


@router.get("/manager/dashboard", response_model=ResourceDashboardResponse)
async def get_dashboard(
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ResourceDashboardResponse:
    use_case = AllocationUseCase(uow.allocations, uow.employees, uow.projects, uow.users)
    return await use_case.get_dashboard(current_user.id)


@router.post(
    "/manager/allocations",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def allocate_employee(
    request: AllocateEmployeeRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> AllocationResponse:
    use_case = AllocationUseCase(uow.allocations, uow.employees, uow.projects, uow.users)
    return await use_case.allocate(current_user.id, request)


@router.get("/manager/allocations", response_model=list[AllocationResponse])
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
    "/manager/allocations/{allocation_id}/end",
    response_model=AllocationResponse,
)
async def end_allocation(
    allocation_id: int,
    request: EndAllocationRequest,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> AllocationResponse:
    use_case = AllocationUseCase(uow.allocations, uow.employees, uow.projects, uow.users)
    return await use_case.end_allocation(current_user.id, allocation_id, request)


@router.post("/manager/employees/{employee_id}/restore-timesheet-access")
async def restore_timesheet_access(
    employee_id: int,
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, str]:
    email = EmailProviderFactory.create()
    email_svc = EmailNotificationService(email, uow.notifications)
    use_case = RestoreTimesheetAccessUseCase(uow.employees, uow.users, email_svc)
    return await use_case.execute(current_user.id, employee_id)  # type: ignore[arg-type]


@router.get("/admin/allocations", response_model=list[AllocationResponse], tags=["admin-allocations"])
async def list_all_allocations(
    employee_id: int | None = None,
    project_id: int | None = None,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[AllocationResponse]:
    """Admin: view all allocations company-wide with optional filters (BRD Screen 3.3)."""
    if employee_id is not None:
        allocations = await uow.allocations.find_by_employee(employee_id)
    elif project_id is not None:
        allocations = await uow.allocations.find_by_project(project_id)
    else:
        allocations = await uow.allocations.find_all()
    return [_to_allocation_response(a) for a in allocations]
