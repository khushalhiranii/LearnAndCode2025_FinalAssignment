from datetime import date, datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base


class AllocationModel(Base):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resource_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resource_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    utilization_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )
