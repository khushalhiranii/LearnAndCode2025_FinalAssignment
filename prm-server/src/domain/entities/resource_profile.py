from dataclasses import dataclass
from datetime import date, datetime

from src.domain.enums import ProficiencyLevel


@dataclass
class ResourceProfile:
    id: int | None
    user_id: int
    full_name: str            # denormalised from User for fast display
    email: str                # denormalised from User
    department: str | None
    designation: str | None
    date_of_joining: date | None
    manager_user_id: int | None    # FK → users.id — direct reporting parent
    is_available: bool             # HR domain: False = on leave / deactivated
    created_at: datetime
    updated_at: datetime


@dataclass
class ResourceSkill:
    """Associative entity: one resource profile ↔ one skill with a proficiency level."""
    id: int | None
    resource_profile_id: int
    skill_id: int
    skill_name: str            # denormalised from Skill for display
    proficiency: ProficiencyLevel
    created_at: datetime
    updated_at: datetime


# Backward-compatible aliases — used by any callers still importing the old names
Employee = ResourceProfile
EmployeeSkill = ResourceSkill
