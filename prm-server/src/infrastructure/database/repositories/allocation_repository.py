from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.allocation import Allocation
from src.domain.enums import AllocationStatus
from src.domain.ports.repositories import IAllocationRepository
from src.infrastructure.database.models.allocation_model import AllocationModel


class SQLAlchemyAllocationRepository(IAllocationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: AllocationModel) -> Allocation:
        return Allocation(
            id=model.id,
            resource_profile_id=model.resource_profile_id,
            project_id=model.project_id,
            utilization_percent=model.utilization_percent,
            from_date=model.from_date,
            to_date=model.to_date,
            status=AllocationStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def find_by_id(self, allocation_id: int) -> Allocation | None:
        result = await self._session.execute(
            select(AllocationModel).where(AllocationModel.id == allocation_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_active_by_employee(self, employee_id: int) -> list[Allocation]:
        result = await self._session.execute(
            select(AllocationModel).where(
                AllocationModel.resource_profile_id == employee_id,
                AllocationModel.status == AllocationStatus.ACTIVE.value,
            )
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_active_by_employee_and_week(
        self,
        employee_id: int,
        week_start: date,
    ) -> list[Allocation]:
        result = await self._session.execute(
            select(AllocationModel).where(
                AllocationModel.resource_profile_id == employee_id,
                AllocationModel.status == AllocationStatus.ACTIVE.value,
                AllocationModel.from_date <= week_start,
                AllocationModel.to_date >= week_start,
            )
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_project(
        self,
        project_id: int,
        active_only: bool = False,
    ) -> list[Allocation]:
        q = select(AllocationModel).where(AllocationModel.project_id == project_id)
        if active_only:
            q = q.where(AllocationModel.status == AllocationStatus.ACTIVE.value)
        result = await self._session.execute(q)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_employee(
        self,
        employee_id: int,
        active_only: bool = False,
    ) -> list[Allocation]:
        q = select(AllocationModel).where(AllocationModel.resource_profile_id == employee_id)
        if active_only:
            q = q.where(AllocationModel.status == AllocationStatus.ACTIVE.value)
        result = await self._session.execute(q)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, allocation: Allocation) -> Allocation:
        model = AllocationModel()
        if allocation.id is not None:
            model.id = allocation.id
        model.resource_profile_id = allocation.resource_profile_id
        model.project_id = allocation.project_id
        model.utilization_percent = allocation.utilization_percent
        model.from_date = allocation.from_date
        model.to_date = allocation.to_date
        model.status = allocation.status.value
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def end_allocation(self, allocation_id: int, ended_at: date) -> None:
        await self._session.execute(
            update(AllocationModel)
            .where(AllocationModel.id == allocation_id)
            .values(
                status=AllocationStatus.ENDED.value,
                to_date=ended_at,
                updated_at=datetime.now(timezone.utc),
            )
        )

    async def find_all(self) -> list[Allocation]:
        result = await self._session.execute(
            select(AllocationModel).order_by(AllocationModel.resource_profile_id)
        )
        return [self._to_entity(m) for m in result.scalars().all()]
