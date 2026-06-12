from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import ProficiencyLevel


@dataclass
class Skill:
    """Master skill definition (shared across all resources)."""
    id: int | None
    name: str
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# EmployeeSkill lives in resource_profile.py; import here for callers that still
# import from skill.py
from src.domain.entities.resource_profile import ResourceSkill as EmployeeSkill  # noqa: F401, E402
