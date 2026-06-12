from datetime import date, datetime, timezone

from src.application.dtos.allocation_dtos import (
    AllocateEmployeeRequest,
    AllocationResponse,
    EmployeeDashboardRow,
    EndAllocationRequest,
    ResourceDashboardResponse,
)
from src.domain.entities.allocation import Allocation
from src.domain.enums import AllocationStatus, ProjectStatus
from src.domain.exceptions import (
    AllocationAlreadyEndedError,
    AllocationNotFoundError,
    AllocationOverlapError,
    AuthorizationError,
    EmployeeNotFoundError,
    InvalidAllocationDateError,
    ProjectNotActiveError,
    ProjectNotFoundError,
)
from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    IProjectRepository,
    IUserRepository,
)


class AllocationUseCase:

    def __init__(
        self,
        allocation_repo: IAllocationRepository,
        employee_repo: IEmployeeRepository,
        project_repo: IProjectRepository,
        user_repo: IUserRepository,
    ) -> None:
        self._allocations = allocation_repo
        self._employees = employee_repo
        self._projects = project_repo
        self._users = user_repo

    # ── allocate ──────────────────────────────────────────────────────────────

    async def allocate(
        self,
        manager_user_id: int,
        request: AllocateEmployeeRequest,
    ) -> AllocationResponse:
        # 1. Validate date range
        if request.from_date >= request.to_date:
            raise InvalidAllocationDateError(
                "from_date must be strictly before to_date."
            )

        # 2. Resource profile must exist and belong to this manager
        employee = await self._employees.find_by_id(request.resource_profile_id)
        if employee is None:
            raise EmployeeNotFoundError(f"Employee {request.resource_profile_id} not found.")
        if employee.manager_user_id != manager_user_id:
            raise AuthorizationError(
                "You can only allocate employees from your own team."
            )
        if not employee.is_available:
            raise EmployeeNotFoundError(
                f"Employee {request.resource_profile_id} is inactive."
            )

        # 3. Project must exist, be ACTIVE, and belong to this manager
        project = await self._projects.find_by_id(request.project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {request.project_id} not found.")
        if project.status not in (ProjectStatus.ACTIVE, ProjectStatus.PLANNED):
            raise ProjectNotActiveError(
                f"Project '{project.name}' must be ACTIVE or PLANNED for allocation "
                f"(current status: {project.status.value})."
            )
        if project.manager_user_id != manager_user_id:
            raise AuthorizationError(
                "You can only allocate to projects you manage."
            )

        # 4. Utilization overlap check (only allocations whose dates overlap)
        active_allocations = await self._allocations.find_active_by_employee(
            request.resource_profile_id
        )
        overlapping = [
            a
            for a in active_allocations
            if _date_ranges_overlap(
                a.from_date, a.to_date, request.from_date, request.to_date
            )
        ]
        current_total = sum(a.utilization_percent for a in overlapping)
        if current_total + request.utilization_percent > 100:
            raise AllocationOverlapError(
                f"Allocation would exceed 100% utilization. "
                f"Current: {current_total}%, Requested: {request.utilization_percent}%, "
                f"Available: {100 - current_total}%."
            )

        now = datetime.now(timezone.utc)
        allocation = Allocation(
            id=None,
            resource_profile_id=request.resource_profile_id,
            project_id=request.project_id,
            utilization_percent=request.utilization_percent,
            from_date=request.from_date,
            to_date=request.to_date,
            status=AllocationStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        saved = await self._allocations.save(allocation)
        return _to_allocation_response(saved)

    # ── end_allocation ────────────────────────────────────────────────────────

    async def end_allocation(
        self,
        manager_user_id: int,
        allocation_id: int,
        request: EndAllocationRequest,
    ) -> AllocationResponse:
        allocation = await self._allocations.find_by_id(allocation_id)
        if allocation is None:
            raise AllocationNotFoundError(f"Allocation {allocation_id} not found.")
        if allocation.status == AllocationStatus.ENDED:
            raise AllocationAlreadyEndedError(
                f"Allocation {allocation_id} is already ended."
            )

        project = await self._projects.find_by_id(allocation.project_id)
        employee = await self._employees.find_by_id(allocation.resource_profile_id)
        is_team_manager = (
            employee is not None and employee.manager_user_id == manager_user_id
        )
        is_project_owner = (
            project is not None and project.manager_user_id == manager_user_id
        )
        if not (is_team_manager or is_project_owner):
            raise AuthorizationError(
                "You can only end allocations for your team or projects you own."
            )

        await self._allocations.end_allocation(allocation_id, request.ended_at)

        # Return the updated entity
        updated = await self._allocations.find_by_id(allocation_id)
        return _to_allocation_response(updated)

    # ── get_dashboard ─────────────────────────────────────────────────────────

    async def get_dashboard(self, manager_user_id: int) -> ResourceDashboardResponse:
        all_employees = await self._employees.find_by_manager(manager_user_id)

        team_rows: list[EmployeeDashboardRow] = []
        bench_count = 0
        allocated_count = 0

        for emp in all_employees:
            user = await self._users.find_by_id(emp.user_id)
            full_name = user.full_name if user else ""
            
            active_allocs = await self._allocations.find_active_by_employee(emp.id)
            total_util = sum(a.utilization_percent for a in active_allocs)
            label = "BENCH" if total_util == 0 else "ALLOCATED"
            if total_util == 0:
                bench_count += 1
            else:
                allocated_count += 1

            emp_skills = await self._employees.find_skills(emp.id)
            skill_labels = [
                f"{s.skill_name} ({s.proficiency.value})" for s in emp_skills
            ]

            team_rows.append(
                EmployeeDashboardRow(
                    resource_profile_id=emp.id,
                    full_name=full_name,
                    designation=emp.designation,
                    department=emp.department,
                    total_utilization_percent=total_util,
                    availability_label=label,
                    skills=skill_labels,
                    active_allocations=[_to_allocation_response(a) for a in active_allocs],
                )
            )

        return ResourceDashboardResponse(
            manager_user_id=manager_user_id,
            total_team_size=len(all_employees),
            bench_count=bench_count,
            allocated_count=allocated_count,
            team=team_rows,
        )


def _date_ranges_overlap(
    a_from: date, a_to: date, b_from: date, b_to: date
) -> bool:
    return a_from <= b_to and b_from <= a_to


def _to_allocation_response(allocation: Allocation) -> AllocationResponse:
    return AllocationResponse(
        id=allocation.id,
        resource_profile_id=allocation.resource_profile_id,
        project_id=allocation.project_id,
        utilization_percent=allocation.utilization_percent,
        from_date=allocation.from_date,
        to_date=allocation.to_date,
        status=allocation.status,
        created_at=allocation.created_at,
        updated_at=allocation.updated_at,
    )
