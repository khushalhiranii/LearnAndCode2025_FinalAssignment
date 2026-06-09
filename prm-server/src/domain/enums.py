from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


# Additional enums added in future sprints:
# EmployeeStatus, ProjectStatus, MilestoneStatus,
# ProficiencyLevel, SkillCategory, TimesheetStatus,
# ProjectHealthStatus, AIRequestType
