from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.enums import AllocationStatus


# ─── Allocation requests ─────────────────────────────────────────────────────

class AllocateEmployeeRequest(BaseModel):
    resource_profile_id: int
    project_id: int
    utilization_percent: int = Field(..., ge=1, le=100)
    from_date: date
    to_date: date


class EndAllocationRequest(BaseModel):
    ended_at: date         # The effective end date (may be today or a past date)


# ─── Allocation responses ─────────────────────────────────────────────────────

class AllocationResponse(BaseModel):
    id: int
    resource_profile_id: int
    project_id: int
    utilization_percent: int
    from_date: date
    to_date: date
    status: AllocationStatus
    created_at: datetime
    updated_at: datetime


# ─── Dashboard responses ──────────────────────────────────────────────────────

class EmployeeDashboardRow(BaseModel):
    resource_profile_id: int
    full_name: str
    designation: str | None
    department: str | None
    total_utilization_percent: int          # 0 = BENCH, >0 = ALLOCATED
    availability_label: str                 # "BENCH" or "ALLOCATED"
    skills: list[str] = Field(default_factory=list)
    active_allocations: list[AllocationResponse]


class ResourceDashboardResponse(BaseModel):
    manager_user_id: int
    total_team_size: int
    bench_count: int
    allocated_count: int
    team: list[EmployeeDashboardRow]
