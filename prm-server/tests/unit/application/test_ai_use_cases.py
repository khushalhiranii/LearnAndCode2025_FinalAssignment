"""Unit tests for AI use cases."""

from datetime import datetime, timezone

import pytest

from src.application.ai.risk_summary_use_case import RiskSummaryUseCase, _rule_based_summary
from src.application.ai.skill_match_use_case import SkillMatchUseCase
from src.application.dtos.ai_dtos import RiskSummaryRequest, SkillMatchRequest
from src.domain.entities.project_health import AISuggestionAudit
from src.domain.entities.resource_profile import ResourceProfile
from src.domain.enums import Role
from src.domain.ports.ai_provider import IAIProvider, RiskSummaryContext
from src.infrastructure.llm.gemma_adapter import MockAIProvider
from tests.conftest import (
    InMemoryAllocationRepository,
    InMemoryEmployeeRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
    make_admin_user,
    make_allocation,
    make_project,
)
from src.domain.enums import ProjectStatus


class InMemoryAuditRepository:
    async def save(self, audit: AISuggestionAudit) -> AISuggestionAudit:
        audit.id = 1
        return audit


class InMemoryHealthRepository:
    async def save_snapshot(self, snapshot):
        return snapshot

    async def find_latest_by_project(self, project_id):
        return None

    async def find_latest_by_projects(self, project_ids):
        return {}


class _FakeTimesheetRepo:
    async def find_by_employee(self, eid):
        return []

    async def find_by_id(self, tid):
        return None


class _FakeMilestoneRepo:
    async def find_by_project(self, pid):
        return []


class FailingAIProvider(IAIProvider):
    @property
    def provider_name(self) -> str:
        return "failing"

    async def rank_resources(self, query, candidates, hours_per_week=None):
        raise RuntimeError("fail")

    async def summarize_risk(self, context):
        raise RuntimeError("fail")


@pytest.mark.asyncio
async def test_skill_match_excludes_over_allocated() -> None:
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    project_repo = InMemoryProjectRepository()
    audit_repo = InMemoryAuditRepository()

    now = datetime.now(timezone.utc)
    emp = ResourceProfile(
        id=10, user_id=3, full_name="Dev", email="d@t.com",
        department=None, designation=None, date_of_joining=None,
        manager_user_id=2, is_available=True, created_at=now, updated_at=now,
    )
    await emp_repo.save(emp)
    await alloc_repo.save(make_allocation(resource_profile_id=10, utilization_percent=100))

    uc = SkillMatchUseCase(
        emp_repo, alloc_repo, _FakeTimesheetRepo(), user_repo,
        project_repo, MockAIProvider(), audit_repo,
    )
    result = await uc.execute(2, SkillMatchRequest(query="Java developer needed"))
    assert result.matches == []


@pytest.mark.asyncio
async def test_skill_match_with_mock_provider() -> None:
    user_repo = InMemoryUserRepository()
    emp_repo = InMemoryEmployeeRepository()
    alloc_repo = InMemoryAllocationRepository()
    project_repo = InMemoryProjectRepository()
    audit_repo = InMemoryAuditRepository()

    now = datetime.now(timezone.utc)
    emp = ResourceProfile(
        id=10, user_id=3, full_name="Dev", email="d@t.com",
        department=None, designation=None, date_of_joining=None,
        manager_user_id=2, is_available=True, created_at=now, updated_at=now,
    )
    await emp_repo.save(emp)

    uc = SkillMatchUseCase(
        emp_repo, alloc_repo, _FakeTimesheetRepo(), user_repo,
        project_repo, MockAIProvider(), audit_repo,
    )
    result = await uc.execute(2, SkillMatchRequest(query="Python backend developer"))
    assert len(result.matches) >= 1
    assert result.ai_generated is True


@pytest.mark.asyncio
async def test_risk_summary_fallback_on_ai_failure() -> None:
    project_repo = InMemoryProjectRepository()
    project = make_project(project_id=1, manager_user_id=2, status=ProjectStatus.ACTIVE)
    await project_repo.save(project)

    uc = RiskSummaryUseCase(
        project_repo,
        _FakeMilestoneRepo(),
        InMemoryAllocationRepository(),
        _FakeTimesheetRepo(),
        InMemoryHealthRepository(),
        FailingAIProvider(),
        InMemoryAuditRepository(),
    )
    result = await uc.execute(2, RiskSummaryRequest(project_id=1))
    assert result.ai_generated is False
    assert "Alpha Project" in result.summary


def test_rule_based_summary_with_flags() -> None:
    ctx = RiskSummaryContext(
        project_name="Test",
        milestones=[],
        resource_effort=[],
        health_status="AT_RISK",
        risk_flags=["Milestone overdue"],
    )
    text = _rule_based_summary(ctx)
    assert "Milestone overdue" in text
