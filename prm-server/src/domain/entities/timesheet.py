from dataclasses import dataclass
from datetime import date, datetime

from src.domain.enums import TimesheetStatus


@dataclass
class ActivityTag:
    id: int | None
    name: str
    category: str
    is_system_tag: bool
    is_active: bool


@dataclass
class TimesheetEntryTag:
    """Represents one activity tag selected on a timesheet entry."""
    activity_tag_id: int
    tag_name: str                    # denormalized from ActivityTag for display
    custom_tag_text: str | None      # non-null only when "Other" tag is selected


@dataclass
class TimesheetEntry:
    id: int | None
    timesheet_id: int | None         # None before the parent Timesheet is persisted
    project_id: int
    hours_worked: float
    tags: list[TimesheetEntryTag]
    created_at: datetime


@dataclass
class Timesheet:
    id: int | None
    resource_profile_id: int
    week_start_date: date
    total_hours: float
    status: TimesheetStatus
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    entries: list[TimesheetEntry]    # populated on find_by_id; empty list on find_by_employee
