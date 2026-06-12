from src.application.dtos.allocation_dtos import AllocationResponse
from src.domain.entities.allocation import Allocation
from src.domain.ports.repositories import IAllocationRepository, IEmployeeRepository


def _to_response(allocation: Allocation) -> AllocationResponse:
    return AllocationResponse(
        id=allocation.id or 0,
        resource_profile_id=allocation.resource_profile_id,
        project_id=allocation.project_id,
        utilization_percent=allocation.utilization_percent,
        from_date=allocation.from_date,
        to_date=allocation.to_date,
        status=allocation.status,
        created_at=allocation.created_at,
        updated_at=allocation.updated_at,
    )


class EmployeeAllocationUseCase:

    def __init__(
        self,
        allocation_repo: IAllocationRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._allocations = allocation_repo
        self._employees = employee_repo

    async def list_my_allocations(self, employee_user_id: int) -> list[AllocationResponse]:
        employee = await self._employees.find_by_user_id(employee_user_id)
        if not employee:
            return []
        
        # Show all allocations for the employee (active and ended)
        allocations = await self._allocations.find_by_employee(employee.id, active_only=False)
        return [_to_response(a) for a in allocations]
