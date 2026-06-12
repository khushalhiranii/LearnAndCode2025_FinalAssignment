from datetime import datetime, timezone

from pydantic import BaseModel, Field


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
