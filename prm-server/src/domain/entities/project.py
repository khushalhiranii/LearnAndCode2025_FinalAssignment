from dataclasses import dataclass
from datetime import date, datetime

from src.domain.enums import ProjectStatus


@dataclass
class Project:
    id: int | None
    name: str
    description: str | None
    manager_user_id: int                  # FK → users.id where role=MANAGER
    status: ProjectStatus
    total_story_points: int               # set by admin at project creation/update
    completed_story_points: int           # derived from DONE milestones; stored for fast reads
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime
