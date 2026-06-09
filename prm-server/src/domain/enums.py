from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"       # allocated or bench — actively employed
    INACTIVE = "INACTIVE"   # deactivated by admin


class ProficiencyLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    EXPERT = "EXPERT"


# Additional enums added in future sprints:
# ProjectStatus, MilestoneStatus, SkillCategory, TimesheetStatus,
# ProjectHealthStatus, AIRequestType
