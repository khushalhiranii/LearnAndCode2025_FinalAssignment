from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.notification import NotificationLog, TimesheetReminderTracking
from src.domain.ports.repositories import INotificationRepository
from src.infrastructure.database.models.notification_model import (
    NotificationLogModel,
    TimesheetReminderTrackingModel,
)


class SQLAlchemyNotificationRepository(INotificationRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def was_sent(
        self,
        notification_type: str,
        recipient_user_id: int,
        subject_id: int,
        reference_key: str,
    ) -> bool:
        result = await self._session.execute(
            select(NotificationLogModel.id).where(
                NotificationLogModel.notification_type == notification_type,
                NotificationLogModel.recipient_user_id == recipient_user_id,
                NotificationLogModel.subject_id == subject_id,
                NotificationLogModel.reference_key == reference_key,
            )
        )
        return result.scalar_one_or_none() is not None

    async def record_sent(self, log: NotificationLog) -> NotificationLog:
        model = NotificationLogModel(
            notification_type=log.notification_type,
            recipient_user_id=log.recipient_user_id,
            subject_id=log.subject_id,
            reference_key=log.reference_key,
            provider=log.provider,
            sent_at=log.sent_at,
        )
        self._session.add(model)
        await self._session.flush()
        log.id = model.id
        return log

    async def get_reminder_tracking(
        self, resource_profile_id: int, week_start_date: date
    ) -> TimesheetReminderTracking | None:
        result = await self._session.execute(
            select(TimesheetReminderTrackingModel).where(
                TimesheetReminderTrackingModel.resource_profile_id == resource_profile_id,
                TimesheetReminderTrackingModel.week_start_date == week_start_date,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return TimesheetReminderTracking(
            id=model.id,
            resource_profile_id=model.resource_profile_id,
            week_start_date=model.week_start_date.isoformat(),
            reminder_count=model.reminder_count,
            last_reminder_sent_at=model.last_reminder_sent_at,
        )

    async def save_reminder_tracking(
        self, tracking: TimesheetReminderTracking
    ) -> TimesheetReminderTracking:
        week = date.fromisoformat(tracking.week_start_date)
        result = await self._session.execute(
            select(TimesheetReminderTrackingModel).where(
                TimesheetReminderTrackingModel.resource_profile_id
                == tracking.resource_profile_id,
                TimesheetReminderTrackingModel.week_start_date == week,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = TimesheetReminderTrackingModel(
                resource_profile_id=tracking.resource_profile_id,
                week_start_date=week,
                reminder_count=tracking.reminder_count,
                last_reminder_sent_at=tracking.last_reminder_sent_at,
            )
            self._session.add(model)
        else:
            model.reminder_count = tracking.reminder_count
            model.last_reminder_sent_at = tracking.last_reminder_sent_at
        await self._session.flush()
        tracking.id = model.id
        return tracking
