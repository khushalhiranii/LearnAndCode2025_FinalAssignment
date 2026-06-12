from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.enums import MilestoneStatus, ProjectStatus


# ─── Project requests ───────────────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    manager_user_id: int
    status: ProjectStatus = ProjectStatus.PLANNED
    total_story_points: int = Field(default=0, ge=0)
    start_date: date | None = None
    end_date: date | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    manager_user_id: int | None = None
    status: ProjectStatus | None = None
    total_story_points: int | None = Field(default=None, ge=0)
    start_date: date | None = None
    end_date: date | None = None


# ─── Project responses ───────────────────────────────────────────────────────

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    manager_user_id: int
    status: ProjectStatus
    total_story_points: int
    completed_story_points: int
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime
    health_status: str | None = None


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int


# ─── Milestone requests ──────────────────────────────────────────────────────

class AddMilestoneRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    story_points: int = Field(default=0, ge=0)


class UpdateMilestoneStatusRequest(BaseModel):
    status: MilestoneStatus


# ─── Milestone response ───────────────────────────────────────────────────────

class MilestoneResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    due_date: date | None
    status: MilestoneStatus
    story_points: int
    created_at: datetime
    updated_at: datetime
