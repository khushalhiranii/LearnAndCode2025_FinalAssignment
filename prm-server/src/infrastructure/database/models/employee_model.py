from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.engine import Base


class EmployeeModel(Base):
    __tablename__ = "employees"

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
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    employee_skills: Mapped[list["EmployeeSkillModel"]] = relationship(
        "EmployeeSkillModel", back_populates="employee", lazy="noload"
    )


class EmployeeSkillModel(Base):
    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
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

    employee: Mapped["EmployeeModel"] = relationship(
        "EmployeeModel", back_populates="employee_skills"
    )
