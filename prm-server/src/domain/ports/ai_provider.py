from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SkillMatchCandidate:
    resource_profile_id: int
    full_name: str
    skills: list[str]
    utilization_percent: int
    free_percent: int
    recent_activity_tags: list[str]
    work_status: str


@dataclass
class SkillMatchResult:
    resource_profile_id: int
    full_name: str
    rank: int
    reason: str


@dataclass
class RiskSummaryContext:
    project_name: str
    milestones: list[dict]
    resource_effort: list[dict]
    health_status: str
    risk_flags: list[str]


class IAIProvider(ABC):

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def rank_resources(
        self,
        query: str,
        candidates: list[SkillMatchCandidate],
        hours_per_week: float | None = None,
    ) -> list[SkillMatchResult]: ...

    @abstractmethod
    async def summarize_risk(self, context: RiskSummaryContext) -> str: ...
