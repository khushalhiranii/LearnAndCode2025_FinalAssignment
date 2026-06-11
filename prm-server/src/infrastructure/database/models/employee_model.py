from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.engine import Base


class ResourceProfileModel(Base):
    __tablename__ = "resource_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_joining: Mapped[date | None] = mapped_column(Date, nullable=True)
    manager_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    resource_skills: Mapped[list["ResourceSkillModel"]] = relationship(
        "ResourceSkillModel", back_populates="resource_profile", lazy="noload"
    )


class ResourceSkillModel(Base):
    __tablename__ = "resource_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resource_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resource_profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False
    )
    proficiency: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    resource_profile: Mapped["ResourceProfileModel"] = relationship(
        "ResourceProfileModel", back_populates="resource_skills"
    )


# Backward-compatible aliases — remove after all callers updated
EmployeeModel = ResourceProfileModel
EmployeeSkillModel = ResourceSkillModel
