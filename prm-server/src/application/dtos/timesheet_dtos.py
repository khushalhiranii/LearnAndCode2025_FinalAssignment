from datetime import date, datetime
from pydantic import BaseModel, Field

from src.domain.enums import TimesheetStatus


# ─── Requests ─────────────────────────────────────────────────────────────────

class TimesheetEntryTagRequest(BaseModel):
    activity_tag_id: int
    custom_tag_text: str | None = None

class TimesheetEntryRequest(BaseModel):
    project_id: int
    hours_worked: float = Field(..., gt=0)
    tags: list[TimesheetEntryTagRequest] = Field(default_factory=list)

class SubmitTimesheetRequest(BaseModel):
    week_start_date: date
    entries: list[TimesheetEntryRequest]


# ─── Responses ────────────────────────────────────────────────────────────────

class ActivityTagResponse(BaseModel):
    id: int
    name: str
    category: str


class TimesheetEntryTagDTO(BaseModel):
    activity_tag_id: int
    tag_name: str
    custom_tag_text: str | None = None


class TimesheetEntryDTO(BaseModel):
    id: int
    project_id: int
    hours_worked: float
    tags: list[TimesheetEntryTagDTO]


class TimesheetResponse(BaseModel):
    id: int
    resource_profile_id: int
    week_start_date: date
    total_hours: float
    status: TimesheetStatus
    submitted_at: datetime | None
    entries: list[TimesheetEntryDTO] = Field(default_factory=list)


class ManagerTimesheetRow(BaseModel):
    resource_profile_id: int
    timesheet_id: int | None = None
    employee_name: str
    project_name: str
    hours: float
    status: TimesheetStatus

class ManagerTimesheetListResponse(BaseModel):
    week_start_date: date
    items: list[ManagerTimesheetRow]
