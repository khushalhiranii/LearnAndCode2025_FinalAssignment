from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


class SkillCategory(str, Enum):
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    DEVOPS = "DEVOPS"
    QA = "QA"
    OTHER = "OTHER"


class ProficiencyLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class ProjectStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MilestoneStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class AllocationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class WorkStatus(str, Enum):
    """Computed at query time from active allocations. Never stored in DB."""
    BENCH = "BENCH"
    ALLOCATED = "ALLOCATED"


class TimesheetStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    MISSED = "MISSED"


class ProjectHealthStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    ATTENTION = "ATTENTION"
    AT_RISK = "AT_RISK"


class TeamGapType(str, Enum):
    SKILL_GAP = "SKILL_GAP"
    AVAILABILITY_GAP = "AVAILABILITY_GAP"


class AIRequestType(str, Enum):
    SKILL_MATCH = "SKILL_MATCH"
    RISK_SUMMARY = "RISK_SUMMARY"
    TEAM_BUILDER = "TEAM_BUILDER"


class NotificationType(str, Enum):
    TIMESHEET_REMINDER_1 = "TIMESHEET_REMINDER_1"
    TIMESHEET_REMINDER_2 = "TIMESHEET_REMINDER_2"
    TIMESHEET_FROZEN = "TIMESHEET_FROZEN"
    PROJECT_AT_RISK = "PROJECT_AT_RISK"
    TIMESHEET_ACCESS_RESTORED = "TIMESHEET_ACCESS_RESTORED"
