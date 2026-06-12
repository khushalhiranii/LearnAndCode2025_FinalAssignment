from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.repositories import (
    IAllocationRepository,
    IEmployeeRepository,
    IMilestoneRepository,
    IProjectRepository,
    ISkillRepository,
    IUserRepository,
    ISystemConfigRepository,
    ITimesheetRepository,
    IActivityTagRepository,
    IProjectHealthRepository,
    IAISuggestionAuditRepository,
)
from src.infrastructure.database.engine import AsyncSessionFactory
from src.infrastructure.database.repositories.allocation_repository import SQLAlchemyAllocationRepository
from src.infrastructure.database.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.database.repositories.milestone_repository import SQLAlchemyMilestoneRepository
from src.infrastructure.database.repositories.project_repository import SQLAlchemyProjectRepository
from src.infrastructure.database.repositories.skill_repository import SQLAlchemySkillRepository
from src.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from src.infrastructure.database.repositories.system_config_repository import SQLAlchemySystemConfigRepository
from src.infrastructure.database.repositories.timesheet_repository import (
    SQLAlchemyActivityTagRepository,
    SQLAlchemyTimesheetRepository,
)
from src.infrastructure.database.repositories.project_health_repository import (
    SQLAlchemyAISuggestionAuditRepository,
    SQLAlchemyProjectHealthRepository,
)


class UnitOfWork:
    """Binds all repositories to a single database session for atomicity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users: IUserRepository = SQLAlchemyUserRepository(session)
        self.employees: IEmployeeRepository = SQLAlchemyEmployeeRepository(session)
        self.skills: ISkillRepository = SQLAlchemySkillRepository(session)
        self.projects: IProjectRepository = SQLAlchemyProjectRepository(session)
        self.milestones: IMilestoneRepository = SQLAlchemyMilestoneRepository(session)
        self.allocations: IAllocationRepository = SQLAlchemyAllocationRepository(session)
        self.system_config: ISystemConfigRepository = SQLAlchemySystemConfigRepository(session)
        self.timesheets: ITimesheetRepository = SQLAlchemyTimesheetRepository(session)
        self.activity_tags: IActivityTagRepository = SQLAlchemyActivityTagRepository(session)
        self.project_health: IProjectHealthRepository = SQLAlchemyProjectHealthRepository(session)
        self.ai_audit: IAISuggestionAuditRepository = SQLAlchemyAISuggestionAuditRepository(session)

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


async def get_unit_of_work() -> AsyncGenerator[UnitOfWork, None]:
    """FastAPI dependency that yields a UnitOfWork per request."""
    async with AsyncSessionFactory() as session:
        uow = UnitOfWork(session)
        try:
            yield uow
            await uow.commit()
        except Exception:
            await uow.rollback()
            raise
