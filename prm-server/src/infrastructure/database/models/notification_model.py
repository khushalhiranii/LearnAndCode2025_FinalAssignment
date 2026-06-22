from datetime import date, datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, TIMESTAMP, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base


class NotificationLogModel(Base):
    __tablename__ = "notification_log"
    __table_args__ = (
        UniqueConstraint(
            "notification_type",
            "recipient_user_id",
            "subject_id",
            "reference_key",
            name="uq_notification_dedup",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reference_key: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )


class TimesheetReminderTrackingModel(Base):
    __tablename__ = "timesheet_reminder_tracking"
    __table_args__ = (
        UniqueConstraint(
            "resource_profile_id",
            "week_start_date",
            name="uq_timesheet_reminder_week",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resource_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resource_profiles.id", ondelete="CASCADE"), nullable=False
    )
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    reminder_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reminder_sent_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
