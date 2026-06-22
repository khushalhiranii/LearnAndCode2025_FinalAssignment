"""Unit tests for natural-language team builder."""

from datetime import datetime, timezone

import pytest

from src.application.ai.team_builder_from_query_use_case import TeamBuilderFromQueryUseCase
from src.application.ai.team_builder_use_case import TeamBuilderUseCase
from src.application.ai.team_query_parser import parse_team_query_rule_based
from src.application.dtos.ai_dtos import TeamBuilderFromQueryRequest
from src.domain.entities.project_health import AISuggestionAudit
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.enums import ProficiencyLevel, TeamGapType
from src.domain.exceptions import TeamQueryParseError
from src.domain.ports.ai_provider import IAIProvider, ParsedTeamRole, SkillCatalogEntry
from tests.conftest import (
    InMemoryAllocationRepository,
    InMemoryEmployeeRepository,
    InMemoryProjectRepository,
    InMemorySkillRepository,
    make_skill,
)
from tests.unit.application.test_ai_use_cases import FailingAIProvider, InMemoryAuditRepository


BANKING_QUERY = (
    "a new banking portal needing a Senior Java Developer, "
    "a DevOps Engineer and a QA tester"
)


def _catalog() -> list[SkillCatalogEntry]:
    return [
        SkillCatalogEntry(skill_id=1, name="Java", category="BACKEND"),
        SkillCatalogEntry(skill_id=2, name="DevOps", category="DEVOPS"),
        SkillCatalogEntry(skill_id=3, name="QA Testing", category="QA"),
    ]


def test_rule_based_parser_banking_portal_example() -> None:
    roles = parse_team_query_rule_based(BANKING_QUERY, _catalog())
    assert len(roles) == 3
    by_skill = {r.skill_id: r for r in roles}
    assert by_skill[1].min_proficiency == ProficiencyLevel.ADVANCED.value
    assert by_skill[2].skill_id == 2
    assert by_skill[3].skill_id == 3


@pytest.mark.asyncio
async def test_from_query_banking_portal_with_rule_based_fallback() -> None:
    emp_repo = InMemoryEmployeeRepository()
    skill_repo = InMemorySkillRepository()
    alloc_repo = InMemoryAllocationRepository()
    project_repo = InMemoryProjectRepository()
    audit_repo = InMemoryAuditRepository()

    for sid, name in [(1, "Java"), (2, "DevOps"), (3, "QA Testing")]:
        await skill_repo.save(make_skill(skill_id=sid, name=name))

    now = datetime.now(timezone.utc)
    for eid, name in [(10, "Alice"), (11, "Bob"), (12, "Carol")]:
        await emp_repo.save(
            ResourceProfile(
                id=eid, user_id=eid + 100, full_name=name, email=f"{name}@t.com",
                department=None, designation=None, date_of_joining=None,
                manager_user_id=2, is_available=True, created_at=now, updated_at=now,
            )
        )
    await emp_repo.add_skill(10, 1, ProficiencyLevel.ADVANCED)
    await emp_repo.add_skill(11, 2, ProficiencyLevel.INTERMEDIATE)
    await emp_repo.add_skill(12, 3, ProficiencyLevel.BEGINNER)

    team_builder = TeamBuilderUseCase(
        emp_repo, alloc_repo, skill_repo, project_repo, audit_repo
    )
    uc = TeamBuilderFromQueryUseCase(
        team_builder, skill_repo, FailingAIProvider()
    )
    result = await uc.execute(2, TeamBuilderFromQueryRequest(query=BANKING_QUERY))

    assert result.ai_parsed is False
    assert len(result.parsed_roles) == 3
    assert result.all_roles_filled is True
    names = {r.full_name for r in result.roles if r.filled}
    assert names == {"Alice", "Bob", "Carol"}


@pytest.mark.asyncio
async def test_from_query_raises_when_nothing_parsed() -> None:
    skill_repo = InMemorySkillRepository()
    team_builder = TeamBuilderUseCase(
        InMemoryEmployeeRepository(),
        InMemoryAllocationRepository(),
        skill_repo,
        InMemoryProjectRepository(),
        InMemoryAuditRepository(),
    )
    uc = TeamBuilderFromQueryUseCase(
        team_builder, skill_repo, FailingAIProvider()
    )
    with pytest.raises(TeamQueryParseError):
        await uc.execute(2, TeamBuilderFromQueryRequest(query="hello world only"))


class _FixedAIParser(IAIProvider):
    @property
    def provider_name(self) -> str:
        return "fixed"

    async def rank_resources(self, query, candidates, hours_per_week=None):
        return []

    async def summarize_risk(self, context):
        return ""

    async def parse_team_requirements(self, query, skills):
        return [
            ParsedTeamRole("Senior Java Developer", 1, "ADVANCED"),
            ParsedTeamRole("DevOps Engineer", 2, "INTERMEDIATE"),
            ParsedTeamRole("QA Tester", 3, "BEGINNER"),
        ]


@pytest.mark.asyncio
async def test_from_query_uses_ai_parser_when_available() -> None:
    skill_repo = InMemorySkillRepository()
    for sid, name in [(1, "Java"), (2, "DevOps"), (3, "QA Testing")]:
        await skill_repo.save(make_skill(skill_id=sid, name=name))

    team_builder = TeamBuilderUseCase(
        InMemoryEmployeeRepository(),
        InMemoryAllocationRepository(),
        skill_repo,
        InMemoryProjectRepository(),
        InMemoryAuditRepository(),
    )
    uc = TeamBuilderFromQueryUseCase(team_builder, skill_repo, _FixedAIParser())
    result = await uc.execute(2, TeamBuilderFromQueryRequest(query=BANKING_QUERY))
    assert result.ai_parsed is True
    assert len(result.parsed_roles) == 3
