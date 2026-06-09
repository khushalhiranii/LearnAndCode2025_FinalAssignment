from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import ProficiencyLevel


@dataclass
class Skill:
    """Master skill definition (shared across all employees)."""
    id: int | None
    name: str       # e.g. "Python", "Project Management"
    category: str   # e.g. "Technical", "Soft Skill"
    created_at: datetime
    updated_at: datetime


@dataclass
class EmployeeSkill:
    """Associative entity: one employee ↔ one skill with a proficiency level."""
    id: int | None
    employee_id: int
    skill_id: int
    skill_name: str          # denormalised for display
    proficiency: ProficiencyLevel
    created_at: datetime
    updated_at: datetime
