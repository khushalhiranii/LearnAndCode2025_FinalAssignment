from datetime import date, datetime, timezone

from pydantic import BaseModel, Field

from src.domain.enums import ProficiencyLevel, TeamGapType


class SkillMatchRequest(BaseModel):
    query: str = Field(min_length=3)
    project_id: int | None = None
    hours_per_week: float | None = Field(None, ge=1, le=168)
    utilization_percent: int | None = Field(None, ge=1, le=100)


class SkillMatchItemResponse(BaseModel):
    rank: int
    resource_profile_id: int
    full_name: str
    reason: str
    free_percent: int


class SkillMatchResponse(BaseModel):
    query: str
    matches: list[SkillMatchItemResponse]
    ai_generated: bool
    note: str = "Suggestions are AI-generated. Verify availability before confirming."


class RiskSummaryRequest(BaseModel):
    project_id: int


class RiskSummaryResponse(BaseModel):
    project_id: int
    project_name: str
    summary: str
    ai_generated: bool
    health_status: str
    risk_flags: list[str]


class ProjectHealthResponse(BaseModel):
    project_id: int
    health_status: str
    risk_flags: list[str]
    computed_at: datetime | None


class TeamRoleRequest(BaseModel):
    role_title: str = Field(min_length=1, max_length=100)
    skill_id: int
    min_proficiency: ProficiencyLevel = ProficiencyLevel.BEGINNER
    utilization_percent: int = Field(default=100, ge=1, le=100)


class TeamBuilderRequest(BaseModel):
    roles: list[TeamRoleRequest] = Field(min_length=1, max_length=20)
    project_id: int | None = None


class TeamRoleMatchResponse(BaseModel):
    role_title: str
    skill_id: int
    skill_name: str
    min_proficiency: str
    filled: bool
    resource_profile_id: int | None = None
    full_name: str | None = None
    proficiency: str | None = None
    free_percent: int | None = None
    reason: str | None = None


class TeamRoleGapResponse(BaseModel):
    role_title: str
    skill_id: int
    skill_name: str
    gap_type: TeamGapType
    message: str
    available_from: date | None = None


class TeamBuilderResponse(BaseModel):
    roles: list[TeamRoleMatchResponse]
    gaps: list[TeamRoleGapResponse]
    all_roles_filled: bool
    note: str = "Verify availability before confirming allocations."


class TeamBuilderFromQueryRequest(BaseModel):
    query: str = Field(min_length=10)
    project_id: int | None = None


class ParsedTeamRoleResponse(BaseModel):
    role_title: str
    skill_id: int
    skill_name: str
    min_proficiency: str
    utilization_percent: int


class TeamBuilderFromQueryResponse(TeamBuilderResponse):
    query: str
    parsed_roles: list[ParsedTeamRoleResponse]
    ai_parsed: bool
