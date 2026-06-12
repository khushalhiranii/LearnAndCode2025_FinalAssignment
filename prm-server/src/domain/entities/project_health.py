from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import ProjectHealthStatus


@dataclass
class ProjectHealthSnapshot:
    id: int | None
    project_id: int
    health_status: ProjectHealthStatus
    risk_flags_json: str | None
    computed_at: datetime


@dataclass
class AISuggestionAudit:
    id: int | None
    request_type: str
    subject_id: int
    input_summary: str
    response_summary: str
    provider: str
    created_at: datetime
