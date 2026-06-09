from abc import ABC, abstractmethod

from src.domain.entities.employee import Employee
from src.domain.entities.skill import EmployeeSkill, Skill
from src.domain.entities.user import User
from src.domain.enums import ProficiencyLevel, Role


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
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """Return (users, total_count) with optional filters."""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Return User if email matches, None otherwise."""

    @abstractmethod
    async def update_active(self, user_id: int, is_active: bool) -> None:
        """Toggle is_active flag."""


class IEmployeeRepository(ABC):

    @abstractmethod
    async def find_by_id(self, employee_id: int) -> Employee | None: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> Employee | None: ...

    @abstractmethod
    async def find_all(
        self,
        is_active: bool | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]: ...

    @abstractmethod
    async def save(self, employee: Employee) -> Employee: ...

    @abstractmethod
    async def update_active(self, employee_id: int, is_active: bool) -> None: ...

    @abstractmethod
    async def update_manager(
        self, employee_id: int, manager_user_id: int | None
    ) -> None: ...

    @abstractmethod
    async def find_skills(self, employee_id: int) -> list[EmployeeSkill]: ...

    @abstractmethod
    async def find_employee_skill(
        self, employee_id: int, skill_id: int
    ) -> EmployeeSkill | None: ...

    @abstractmethod
    async def add_skill(
        self,
        employee_id: int,
        skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> EmployeeSkill: ...

    @abstractmethod
    async def update_skill_proficiency(
        self,
        employee_skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> None: ...

    @abstractmethod
    async def remove_skill(self, employee_skill_id: int) -> None: ...


class ISkillRepository(ABC):

    @abstractmethod
    async def find_by_id(self, skill_id: int) -> Skill | None: ...

    @abstractmethod
    async def find_all(self) -> list[Skill]: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Skill | None: ...

    @abstractmethod
    async def save(self, skill: Skill) -> Skill: ...
