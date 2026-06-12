from abc import ABC, abstractmethod
from datetime import date

from src.domain.entities.allocation import Allocation
from src.domain.entities.resource_profile import ResourceProfile, ResourceSkill
from src.domain.entities.milestone import Milestone
from src.domain.entities.project import Project
from src.domain.entities.skill import Skill
from src.domain.entities.user import User
from src.domain.entities.system_config import SystemConfig
from src.domain.entities.project_health import AISuggestionAudit, ProjectHealthSnapshot
from src.domain.entities.timesheet import Timesheet, ActivityTag
from src.domain.enums import AllocationStatus, MilestoneStatus, ProficiencyLevel, ProjectStatus, Role

# Backward-compatible alias
Employee = ResourceProfile
EmployeeSkill = ResourceSkill


class IUserRepository(ABC):

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        """Return User if found, None otherwise."""

    @abstractmethod
    async def find_by_id(self, user_id: int) -> User | None:
        """Return User if found, None otherwise."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist new user or update existing one. Returns saved entity."""

    @abstractmethod
    async def update_password(
        self,
        user_id: int,
        new_password_hash: str,
        force_password_change: bool,
    ) -> None:
        """Update password hash and force_password_change flag atomically."""

    @abstractmethod
    async def find_all(
        self,
        role: Role | None = None,
        is_account_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """Return (users, total_count) with optional filters."""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Return User if email matches, None otherwise."""

    @abstractmethod
    async def update_active(self, user_id: int, is_account_enabled: bool) -> None:
        """Toggle is_account_enabled flag."""

    @abstractmethod
    async def find_active_role(self, user_id: int) -> Role | None:
        """Return currently active Role from user_roles (to_date IS NULL), or None."""

    @abstractmethod
    async def assign_role(
        self,
        user_id: int,
        role: Role,
        from_date: date,
        granted_by_user_id: int | None,
        reason: str | None,
    ) -> None:
        """Insert a new user_roles row for the given role (closes previous active row)."""


class IEmployeeRepository(ABC):

    @abstractmethod
    async def find_by_id(self, employee_id: int) -> ResourceProfile | None: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> ResourceProfile | None: ...

    @abstractmethod
    async def find_all(
        self,
        is_active: bool | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ResourceProfile], int]: ...

    @abstractmethod
    async def save(self, employee: ResourceProfile) -> ResourceProfile: ...

    @abstractmethod
    async def update_active(self, employee_id: int, is_active: bool) -> None: ...

    @abstractmethod
    async def update_manager(
        self, employee_id: int, manager_user_id: int | None
    ) -> None: ...

    @abstractmethod
    async def find_skills(self, employee_id: int) -> list[ResourceSkill]: ...

    @abstractmethod
    async def find_employee_skill(
        self, employee_id: int, skill_id: int
    ) -> ResourceSkill | None: ...

    @abstractmethod
    async def add_skill(
        self,
        employee_id: int,
        skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> ResourceSkill: ...

    @abstractmethod
    async def update_skill_proficiency(
        self,
        employee_skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> None: ...

    @abstractmethod
    async def remove_skill(self, employee_skill_id: int) -> None: ...

    @abstractmethod
    async def find_by_manager(self, manager_user_id: int) -> list[ResourceProfile]:
        """Return all active resource profiles whose manager_user_id matches."""
        ...


class ISkillRepository(ABC):

    @abstractmethod
    async def find_by_id(self, skill_id: int) -> Skill | None: ...

    @abstractmethod
    async def find_all(self) -> list[Skill]: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Skill | None: ...

    @abstractmethod
    async def save(self, skill: Skill) -> Skill: ...


class IAllocationRepository(ABC):

    @abstractmethod
    async def find_by_id(self, allocation_id: int) -> Allocation | None: ...

    @abstractmethod
    async def find_active_by_employee(self, employee_id: int) -> list[Allocation]:
        """Return all ACTIVE allocations for this employee."""
        ...

    @abstractmethod
    async def find_active_by_employee_and_week(
        self,
        employee_id: int,
        week_start: date,
    ) -> list[Allocation]:
        """Return ACTIVE allocations for the employee whose date range covers week_start."""
        ...

    @abstractmethod
    async def find_by_project(
        self,
        project_id: int,
        active_only: bool = False,
    ) -> list[Allocation]:
        """Return allocations for a project; set active_only=True to filter."""
        ...

    @abstractmethod
    async def find_by_employee(
        self,
        employee_id: int,
        active_only: bool = False,
    ) -> list[Allocation]: ...

    @abstractmethod
    async def save(self, allocation: Allocation) -> Allocation: ...

    @abstractmethod
    async def end_allocation(self, allocation_id: int, ended_at: date) -> None:
        """Set status=ENDED and to_date=ended_at."""
        ...

    @abstractmethod
    async def find_all(self) -> list[Allocation]:
        """Return every allocation row (admin use only)."""
        ...


class IProjectRepository(ABC):

    @abstractmethod
    async def find_by_id(self, project_id: int) -> Project | None: ...

    @abstractmethod
    async def find_all(
        self,
        status: ProjectStatus | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Project], int]: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Project | None: ...

    @abstractmethod
    async def save(self, project: Project) -> Project: ...

    @abstractmethod
    async def update_status(self, project_id: int, status: ProjectStatus) -> None: ...

    @abstractmethod
    async def update_completed_points(self, project_id: int, points: int) -> None: ...


class IMilestoneRepository(ABC):

    @abstractmethod
    async def find_by_id(self, milestone_id: int) -> Milestone | None: ...

    @abstractmethod
    async def find_by_project(self, project_id: int) -> list[Milestone]: ...

    @abstractmethod
    async def save(self, milestone: Milestone) -> Milestone: ...

    @abstractmethod
    async def update_status(
        self, milestone_id: int, status: MilestoneStatus
    ) -> None: ...

    @abstractmethod
    async def sum_done_story_points(self, project_id: int) -> int:
        """Return the sum of story_points for all DONE milestones in this project."""
        ...


class ISystemConfigRepository(ABC):

    @abstractmethod
    async def get_config(self) -> SystemConfig:
        """Return the system configuration. Creates defaults if none exist."""

    @abstractmethod
    async def update_config(self, config: SystemConfig) -> SystemConfig:
        """Updates the system configuration."""


class ITimesheetRepository(ABC):

    @abstractmethod
    async def find_by_id(self, timesheet_id: int) -> Timesheet | None:
        """Return full Timesheet with entries and tags populated, or None."""
        ...

    @abstractmethod
    async def find_by_employee_and_week(
        self,
        employee_id: int,
        week_start: date,
    ) -> Timesheet | None:
        """Return the timesheet for this employee+week, or None if not submitted."""
        ...

    @abstractmethod
    async def find_by_employee(self, employee_id: int) -> list[Timesheet]:
        """Return all timesheets for the employee, entries list is empty (summary only)."""
        ...

    @abstractmethod
    async def save(self, timesheet: Timesheet) -> Timesheet:
        """Persist the Timesheet with all entries and tags atomically. Returns saved entity."""
        ...


class IActivityTagRepository(ABC):

    @abstractmethod
    async def find_all_active(self) -> list[ActivityTag]:
        """Return all active activity tags ordered by name."""
        ...

    @abstractmethod
    async def find_by_ids(self, ids: list[int]) -> list[ActivityTag]:
        """Return tags matching the given IDs. Missing IDs are silently omitted."""
        ...


class IProjectHealthRepository(ABC):

    @abstractmethod
    async def save_snapshot(self, snapshot: ProjectHealthSnapshot) -> ProjectHealthSnapshot: ...

    @abstractmethod
    async def find_latest_by_project(self, project_id: int) -> ProjectHealthSnapshot | None: ...

    @abstractmethod
    async def find_latest_by_projects(
        self, project_ids: list[int]
    ) -> dict[int, ProjectHealthSnapshot]: ...


class IAISuggestionAuditRepository(ABC):

    @abstractmethod
    async def save(self, audit: AISuggestionAudit) -> AISuggestionAudit: ...
