from datetime import date, datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, Text, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.engine import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_story_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_story_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    milestones: Mapped[list["MilestoneModel"]] = relationship(
        "MilestoneModel", back_populates="project", lazy="noload"
    )
