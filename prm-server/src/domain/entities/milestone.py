from dataclasses import dataclass
from datetime import date, datetime

from src.domain.enums import MilestoneStatus


@dataclass
class Milestone:
    id: int | None
    project_id: int
    title: str
    description: str | None
    due_date: date | None
    status: MilestoneStatus
    story_points: int                     # points this milestone contributes when DONE
    created_at: datetime
    updated_at: datetime
