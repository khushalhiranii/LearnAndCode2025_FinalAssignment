"""Unit tests for allocation and dashboard use cases (Sprint 4)."""

import pytest
from datetime import date, datetime, timezone

from src.application.dtos.allocation_dtos import (
    AllocateEmployeeRequest,
    EndAllocationRequest,
)
from src.application.manager.allocation_use_case import AllocationUseCase
from src.domain.enums import AllocationStatus, ProjectStatus, Role
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
from tests.conftest import (
    InMemoryAllocationRepository,
    InMemoryEmployeeRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
    make_allocation,
    make_project,
)


# ── helpers ───────────────────────────────────────────────────────────────────

MANAGER_USER_ID = 99


def _make_active_employee(employee_id: int = 10, manager_user_id: int = MANAGER_USER_ID):
    from src.domain.entities.resource_profile import ResourceProfile
    now = datetime.now(timezone.utc)
    return ResourceProfile(
        id=employee_id,
        user_id=employee_id + 100,
        full_name="Alice",
        email=f"alice{employee_id}@x.com",
        department="Engineering",
        designation="Developer",
        date_of_joining=date(2024, 1, 1),
        manager_user_id=manager_user_id,
        is_available=True,
        created_at=now,
        updated_at=now,
    )


def _use_case(alloc_repo, emp_repo, proj_repo):
    return AllocationUseCase(alloc_repo, emp_repo, proj_repo, InMemoryUserRepository())


def _make_request(resource_profile_id=10, project_id=1, utilization=50):
    return AllocateEmployeeRequest(
        resource_profile_id=resource_profile_id,
        project_id=project_id,
        utilization_percent=utilization,
        from_date=date(2026, 7, 1),
        to_date=date(2026, 12, 31),
    )


def _make_active_project(project_id: int = 1, manager_user_id: int = MANAGER_USER_ID):
    return make_project(
        project_id=project_id,
        manager_user_id=manager_user_id,
        status=ProjectStatus.ACTIVE,
    )


# ── allocate tests ────────────────────────────────────────────────────────────


async def test_allocate_creates_active_allocation():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = _make_active_project()
    await proj_repo.save(proj)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    result = await use_case.allocate(MANAGER_USER_ID, _make_request())

    assert result.id is not None
    assert result.status == AllocationStatus.ACTIVE
    assert result.utilization_percent == 50


async def test_allocate_rejects_invalid_date_range():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    req = AllocateEmployeeRequest(
        resource_profile_id=10, project_id=1, utilization_percent=50,
        from_date=date(2026, 12, 31), to_date=date(2026, 7, 1),   # reversed
    )
    with pytest.raises(InvalidAllocationDateError):
        await use_case.allocate(MANAGER_USER_ID, req)


async def test_allocate_rejects_employee_from_other_team():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee(manager_user_id=999)  # different manager
    await emp_repo.save(emp)
    proj = _make_active_project()
    await proj_repo.save(proj)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(AuthorizationError):
        await use_case.allocate(MANAGER_USER_ID, _make_request())


async def test_allocate_rejects_project_from_other_manager():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = _make_active_project(manager_user_id=999)  # different manager
    await proj_repo.save(proj)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(AuthorizationError):
        await use_case.allocate(MANAGER_USER_ID, _make_request())


async def test_allocate_rejects_non_active_or_planned_project():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = make_project(project_id=1, manager_user_id=MANAGER_USER_ID, status=ProjectStatus.ON_HOLD)
    await proj_repo.save(proj)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(ProjectNotActiveError):
        await use_case.allocate(MANAGER_USER_ID, _make_request())


async def test_allocate_allows_planned_project():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = make_project(project_id=1, manager_user_id=MANAGER_USER_ID, status=ProjectStatus.PLANNED)
    await proj_repo.save(proj)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    result = await use_case.allocate(MANAGER_USER_ID, _make_request())
    assert result.status == AllocationStatus.ACTIVE


async def test_allocate_rejects_when_utilization_would_exceed_100():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = _make_active_project()
    await proj_repo.save(proj)

    # Pre-seed an existing 60% allocation
    existing = make_allocation(resource_profile_id=10, project_id=1, utilization_percent=60)
    await alloc_repo.save(existing)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(AllocationOverlapError):
        # 60 + 50 = 110 > 100
        await use_case.allocate(MANAGER_USER_ID, _make_request(utilization=50))


async def test_allocate_allows_exactly_100_percent():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = _make_active_project()
    await proj_repo.save(proj)

    # Pre-seed a 50% allocation
    existing = make_allocation(resource_profile_id=10, project_id=1, utilization_percent=50)
    await alloc_repo.save(existing)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    # 50 + 50 = 100 — should succeed
    result = await use_case.allocate(MANAGER_USER_ID, _make_request(utilization=50))
    assert result.status == AllocationStatus.ACTIVE


async def test_allocate_raises_for_unknown_employee():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(EmployeeNotFoundError):
        await use_case.allocate(MANAGER_USER_ID, _make_request())


async def test_allocate_raises_for_unknown_project():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(ProjectNotFoundError):
        await use_case.allocate(MANAGER_USER_ID, _make_request())


# ── end_allocation tests ──────────────────────────────────────────────────────


async def test_end_allocation_sets_ended_status():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    alloc = make_allocation(resource_profile_id=10)
    await alloc_repo.save(alloc)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    result = await use_case.end_allocation(
        MANAGER_USER_ID, alloc.id, EndAllocationRequest(ended_at=date(2026, 8, 1))
    )
    assert result.status == AllocationStatus.ENDED


async def test_end_allocation_raises_when_already_ended():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    alloc = make_allocation(resource_profile_id=10, status=AllocationStatus.ENDED)
    await alloc_repo.save(alloc)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(AllocationAlreadyEndedError):
        await use_case.end_allocation(
            MANAGER_USER_ID, alloc.id, EndAllocationRequest(ended_at=date(2026, 8, 1))
        )


async def test_end_allocation_raises_for_unknown():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(AllocationNotFoundError):
        await use_case.end_allocation(
            MANAGER_USER_ID, 999, EndAllocationRequest(ended_at=date(2026, 8, 1))
        )


async def test_allocate_allows_non_overlapping_date_ranges_over_100_total():
    """Two 100% allocations in different periods should not conflict."""
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    proj = _make_active_project()
    await proj_repo.save(proj)
    proj2 = _make_active_project(project_id=2)
    await proj_repo.save(proj2)

    existing = make_allocation(
        resource_profile_id=10,
        project_id=1,
        utilization_percent=100,
    )
    existing.from_date = date(2026, 1, 1)
    existing.to_date = date(2026, 6, 30)
    await alloc_repo.save(existing)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    req = AllocateEmployeeRequest(
        resource_profile_id=10,
        project_id=2,
        utilization_percent=100,
        from_date=date(2026, 7, 1),
        to_date=date(2026, 12, 31),
    )
    result = await use_case.allocate(MANAGER_USER_ID, req)
    assert result.status == AllocationStatus.ACTIVE


async def test_end_allocation_allows_project_owner_not_team_manager():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    project_owner_id = MANAGER_USER_ID
    other_manager_id = 888
    emp = _make_active_employee(manager_user_id=other_manager_id)
    await emp_repo.save(emp)
    proj = _make_active_project(manager_user_id=project_owner_id)
    await proj_repo.save(proj)
    alloc = make_allocation(resource_profile_id=10, project_id=1)
    await alloc_repo.save(alloc)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    result = await use_case.end_allocation(
        project_owner_id,
        alloc.id,
        EndAllocationRequest(ended_at=date(2026, 8, 1)),
    )
    assert result.status == AllocationStatus.ENDED


async def test_end_allocation_raises_for_other_team():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee(manager_user_id=999)  # belongs to different manager
    await emp_repo.save(emp)
    alloc = make_allocation(resource_profile_id=10)
    await alloc_repo.save(alloc)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    with pytest.raises(AuthorizationError):
        await use_case.end_allocation(
            MANAGER_USER_ID, alloc.id, EndAllocationRequest(ended_at=date(2026, 8, 1))
        )


# ── dashboard tests ───────────────────────────────────────────────────────────


async def test_dashboard_bench_employee_shows_zero_utilization():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    # No allocations — employee is bench

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    result = await use_case.get_dashboard(MANAGER_USER_ID)

    assert result.total_team_size == 1
    assert result.bench_count == 1
    assert result.allocated_count == 0
    assert result.team[0].availability_label == "BENCH"
    assert result.team[0].total_utilization_percent == 0


async def test_dashboard_allocated_employee_shows_correct_utilization():
    alloc_repo = InMemoryAllocationRepository()
    emp_repo = InMemoryEmployeeRepository()
    proj_repo = InMemoryProjectRepository()

    emp = _make_active_employee()
    await emp_repo.save(emp)
    alloc = make_allocation(resource_profile_id=10, utilization_percent=75)
    await alloc_repo.save(alloc)

    use_case = _use_case(alloc_repo, emp_repo, proj_repo)
    result = await use_case.get_dashboard(MANAGER_USER_ID)

    assert result.bench_count == 0
    assert result.allocated_count == 1
    assert result.team[0].availability_label == "ALLOCATED"
    assert result.team[0].total_utilization_percent == 75
    assert len(result.team[0].active_allocations) == 1
