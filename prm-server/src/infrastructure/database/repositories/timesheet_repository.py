from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.timesheet import (
    ActivityTag,
    Timesheet,
    TimesheetEntry,
    TimesheetEntryTag,
)
from src.domain.enums import TimesheetStatus
from src.domain.ports.repositories import IActivityTagRepository, ITimesheetRepository
from src.infrastructure.database.models.timesheet_model import (
    ActivityTagModel,
    TimesheetEntryActivityTagModel,
    TimesheetEntryModel,
    TimesheetModel,
)


class SQLAlchemyTimesheetRepository(ITimesheetRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── private mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _tag_to_entity(
        tag_model: TimesheetEntryActivityTagModel,
        tag_name: str,
    ) -> TimesheetEntryTag:
        return TimesheetEntryTag(
            activity_tag_id=tag_model.activity_tag_id,
            tag_name=tag_name,
            custom_tag_text=tag_model.custom_tag_text,
        )

    @staticmethod
    def _entry_to_entity(
        model: TimesheetEntryModel,
        tag_names: dict[int, str],
    ) -> TimesheetEntry:
        return TimesheetEntry(
            id=model.id,
            timesheet_id=model.timesheet_id,
            project_id=model.project_id,
            hours_worked=model.hours_worked,
            tags=[
                SQLAlchemyTimesheetRepository._tag_to_entity(
                    t, tag_names.get(t.activity_tag_id, "")
                )
                for t in model.entry_tags
            ],
            created_at=model.created_at,
        )

    @staticmethod
    def _to_entity(model: TimesheetModel, with_entries: bool = False) -> Timesheet:
        return Timesheet(
            id=model.id,
            resource_profile_id=model.resource_profile_id,
            week_start_date=model.week_start_date,
            total_hours=model.total_hours,
            status=TimesheetStatus(model.status),
            submitted_at=model.submitted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            entries=[],  # populated separately when with_entries=True
        )

    async def _load_tag_names(self, timesheet_model: TimesheetModel) -> dict[int, str]:
        """Fetch tag names for all entry tags in this timesheet."""
        all_tag_ids = {
            t.activity_tag_id
            for e in timesheet_model.entries
            for t in e.entry_tags
        }
        if not all_tag_ids:
            return {}
        result = await self._session.execute(
            select(ActivityTagModel).where(ActivityTagModel.id.in_(all_tag_ids))
        )
        return {m.id: m.name for m in result.scalars().all()}

    # ── ITimesheetRepository ─────────────────────────────────────────────────

    async def find_by_id(self, timesheet_id: int) -> Timesheet | None:
        result = await self._session.execute(
            select(TimesheetModel)
            .options(
                selectinload(TimesheetModel.entries).selectinload(
                    TimesheetEntryModel.entry_tags
                )
            )
            .where(TimesheetModel.id == timesheet_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        tag_names = await self._load_tag_names(model)
        timesheet = self._to_entity(model)
        timesheet.entries = [
            self._entry_to_entity(e, tag_names) for e in model.entries
        ]
        return timesheet

    async def find_by_employee_and_week(
        self,
        employee_id: int,
        week_start: date,
    ) -> Timesheet | None:
        result = await self._session.execute(
            select(TimesheetModel).where(
                TimesheetModel.resource_profile_id == employee_id,
                TimesheetModel.week_start_date == week_start,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_employee(self, employee_id: int) -> list[Timesheet]:
        result = await self._session.execute(
            select(TimesheetModel)
            .where(TimesheetModel.resource_profile_id == employee_id)
            .order_by(TimesheetModel.week_start_date.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, timesheet: Timesheet) -> Timesheet:
        now = datetime.now(timezone.utc)

        # Insert timesheet header
        ts_model = TimesheetModel(
            resource_profile_id=timesheet.resource_profile_id,
            week_start_date=timesheet.week_start_date,
            total_hours=timesheet.total_hours,
            status=timesheet.status.value,
            submitted_at=timesheet.submitted_at,
            created_at=now,
            updated_at=now,
        )
        self._session.add(ts_model)
        await self._session.flush()

        for entry in timesheet.entries:
            entry_model = TimesheetEntryModel(
                timesheet_id=ts_model.id,
                project_id=entry.project_id,
                hours_worked=entry.hours_worked,
                created_at=now,
                updated_at=now,
            )
            self._session.add(entry_model)
            await self._session.flush()

            for tag in entry.tags:
                tag_model = TimesheetEntryActivityTagModel(
                    timesheet_entry_id=entry_model.id,
                    activity_tag_id=tag.activity_tag_id,
                    custom_tag_text=tag.custom_tag_text,
                )
                self._session.add(tag_model)

        await self._session.flush()
        return await self.find_by_id(ts_model.id)


class SQLAlchemyActivityTagRepository(IActivityTagRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: ActivityTagModel) -> ActivityTag:
        return ActivityTag(
            id=model.id,
            name=model.name,
            category=model.category,
            is_system_tag=model.is_system_tag,
            is_active=model.is_active,
        )

    async def find_all_active(self) -> list[ActivityTag]:
        result = await self._session.execute(
            select(ActivityTagModel)
            .where(ActivityTagModel.is_active == True)
            .order_by(ActivityTagModel.name)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_ids(self, ids: list[int]) -> list[ActivityTag]:
        if not ids:
            return []
        result = await self._session.execute(
            select(ActivityTagModel).where(ActivityTagModel.id.in_(ids))
        )
        return [self._to_entity(m) for m in result.scalars().all()]
