"""Unit tests for Team Builder use case and matcher."""

from datetime import date, datetime, timezone

import pytest

from src.application.ai.team_builder_matcher import TeamMemberPool, TeamRoleSlot, match_team
from src.application.ai.team_builder_use_case import TeamBuilderUseCase
from src.application.dtos.ai_dtos import TeamBuilderRequest, TeamRoleRequest
from src.domain.entities.project_health import AISuggestionAudit
from src.domain.entities.allocation import Allocation
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.enums import ProficiencyLevel, TeamGapType
from tests.conftest import (
    InMemoryAllocationRepository,
    InMemoryEmployeeRepository,
    InMemoryProjectRepository,
    InMemorySkillRepository,
    make_allocation,
    make_skill,
)


class InMemoryAuditRepository:
    async def save(self, audit: AISuggestionAudit) -> AISuggestionAudit:
        audit.id = 1
        return audit


def _employee(
    emp_id: int,
    manager_id: int = 2,
    name: str = "Dev",
) -> ResourceProfile:
    now = datetime.now(timezone.utc)
    return ResourceProfile(
        id=emp_id,
        user_id=emp_id + 100,
        full_name=name,
        email=f"{name.lower()}@test.com",
        department=None,
        designation=None,
        date_of_joining=None,
        manager_user_id=manager_id,
        is_available=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_team_builder_fills_all_roles_without_overlap() -> None:
    emp_repo = InMemoryEmployeeRepository()
    skill_repo = InMemorySkillRepository()
    alloc_repo = InMemoryAllocationRepository()
    project_repo = InMemoryProjectRepository()
    audit_repo = InMemoryAuditRepository()

    java = make_skill(skill_id=1, name="Java")
    devops = make_skill(skill_id=2, name="DevOps")
    qa = make_skill(skill_id=3, name="QA Testing")
    await skill_repo.save(java)
    await skill_repo.save(devops)
    await skill_repo.save(qa)

    await emp_repo.save(_employee(10, name="Alice"))
    await emp_repo.save(_employee(11, name="Bob"))
    await emp_repo.save(_employee(12, name="Carol"))
    await emp_repo.add_skill(10, 1, ProficiencyLevel.ADVANCED)
    await emp_repo.add_skill(11, 2, ProficiencyLevel.INTERMEDIATE)
    await emp_repo.add_skill(12, 3, ProficiencyLevel.BEGINNER)

    uc = TeamBuilderUseCase(emp_repo, alloc_repo, skill_repo, project_repo, audit_repo)
    result = await uc.execute(
        2,
        TeamBuilderRequest(
            roles=[
                TeamRoleRequest(role_title="Senior Java Developer", skill_id=1, min_proficiency=ProficiencyLevel.ADVANCED),
                TeamRoleRequest(role_title="DevOps Engineer", skill_id=2),
                TeamRoleRequest(role_title="QA Tester", skill_id=3),
            ]
        ),
    )

    assert result.all_roles_filled is True
    assert len(result.gaps) == 0
    names = {r.full_name for r in result.roles if r.filled}
    assert names == {"Alice", "Bob", "Carol"}


@pytest.mark.asyncio
async def test_team_builder_skill_gap() -> None:
    emp_repo = InMemoryEmployeeRepository()
    skill_repo = InMemorySkillRepository()
    alloc_repo = InMemoryAllocationRepository()
    project_repo = InMemoryProjectRepository()
    audit_repo = InMemoryAuditRepository()

    skill = make_skill(skill_id=1, name="Rust")
    await skill_repo.save(skill)
    await emp_repo.save(_employee(10, name="Alice"))
    await emp_repo.add_skill(10, 1, ProficiencyLevel.BEGINNER)

    uc = TeamBuilderUseCase(emp_repo, alloc_repo, skill_repo, project_repo, audit_repo)
    result = await uc.execute(
        2,
        TeamBuilderRequest(
            roles=[
                TeamRoleRequest(role_title="Rust Lead", skill_id=1, min_proficiency=ProficiencyLevel.ADVANCED),
            ]
        ),
    )

    assert result.all_roles_filled is False
    assert len(result.gaps) == 1
    assert result.gaps[0].gap_type == TeamGapType.SKILL_GAP
    assert "Consider hiring or training" in result.gaps[0].message


@pytest.mark.asyncio
async def test_team_builder_availability_gap() -> None:
    emp_repo = InMemoryEmployeeRepository()
    skill_repo = InMemorySkillRepository()
    alloc_repo = InMemoryAllocationRepository()
    project_repo = InMemoryProjectRepository()
    audit_repo = InMemoryAuditRepository()

    skill = make_skill(skill_id=1, name="Java")
    await skill_repo.save(skill)
    await emp_repo.save(_employee(10, name="Alice"))
    await emp_repo.add_skill(10, 1, ProficiencyLevel.ADVANCED)
    alloc = make_allocation(resource_profile_id=10, utilization_percent=100)
    alloc = Allocation(
        id=alloc.id,
        resource_profile_id=alloc.resource_profile_id,
        project_id=alloc.project_id,
        utilization_percent=100,
        from_date=alloc.from_date,
        to_date=date(2026, 8, 15),
        status=alloc.status,
        created_at=alloc.created_at,
        updated_at=alloc.updated_at,
    )
    await alloc_repo.save(alloc)

    uc = TeamBuilderUseCase(emp_repo, alloc_repo, skill_repo, project_repo, audit_repo)
    result = await uc.execute(
        2,
        TeamBuilderRequest(
            roles=[TeamRoleRequest(role_title="Java Developer", skill_id=1)],
        ),
    )

    assert result.all_roles_filled is False
    assert len(result.gaps) == 1
    assert result.gaps[0].gap_type == TeamGapType.AVAILABILITY_GAP
    assert result.gaps[0].available_from == date(2026, 8, 15)
    assert "Alice" in result.gaps[0].message


def test_matcher_no_duplicate_assignment() -> None:
    roles = [
        TeamRoleSlot("Java Dev 1", 1, "Java", ProficiencyLevel.BEGINNER, 100),
        TeamRoleSlot("Java Dev 2", 1, "Java", ProficiencyLevel.BEGINNER, 100),
    ]
    members = [
        TeamMemberPool(10, "Only Java Dev", {1: ProficiencyLevel.ADVANCED}, 100, None),
        TeamMemberPool(11, "Other Skill", {2: ProficiencyLevel.BEGINNER}, 100, None),
    ]
    outcome = match_team(roles, members)

    assert len(outcome.assignments) == 1
    assert 0 in outcome.unfilled_reasons


def test_matcher_picks_higher_proficiency() -> None:
    roles = [
        TeamRoleSlot("Java Dev", 1, "Java", ProficiencyLevel.BEGINNER, 80),
    ]
    members = [
        TeamMemberPool(10, "Junior", {1: ProficiencyLevel.BEGINNER}, 100, None),
        TeamMemberPool(11, "Senior", {1: ProficiencyLevel.ADVANCED}, 80, None),
    ]
    outcome = match_team(roles, members)

    assert outcome.assignments[0] == 1
