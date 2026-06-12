from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, Date, Float, ForeignKey,
    Integer, String, Text, TIMESTAMP, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.engine import Base


class ActivityTagModel(Base):
    __tablename__ = "activity_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_system_tag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TimesheetModel(Base):
    __tablename__ = "timesheets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resource_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resource_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_hours: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="SUBMITTED")
    submitted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    entries: Mapped[list["TimesheetEntryModel"]] = relationship(
        "TimesheetEntryModel", back_populates="timesheet", lazy="noload"
    )


class TimesheetEntryModel(Base):
    __tablename__ = "timesheet_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timesheet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("timesheets.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    hours_worked: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )

    timesheet: Mapped["TimesheetModel"] = relationship(
        "TimesheetModel", back_populates="entries"
    )
    entry_tags: Mapped[list["TimesheetEntryActivityTagModel"]] = relationship(
        "TimesheetEntryActivityTagModel", back_populates="entry", lazy="noload"
    )


class TimesheetEntryActivityTagModel(Base):
    __tablename__ = "timesheet_entry_activity_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timesheet_entry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("timesheet_entries.id", ondelete="CASCADE"), nullable=False
    )
    activity_tag_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("activity_tags.id", ondelete="RESTRICT"), nullable=False
    )
    custom_tag_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    entry: Mapped["TimesheetEntryModel"] = relationship(
        "TimesheetEntryModel", back_populates="entry_tags"
    )
