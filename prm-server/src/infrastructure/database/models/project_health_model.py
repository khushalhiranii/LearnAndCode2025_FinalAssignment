from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base


class ProjectHealthSnapshotModel(Base):
    __tablename__ = "project_health_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    health_status: Mapped[str] = mapped_column(String(15), nullable=False)
    risk_flags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )


class AISuggestionAuditModel(Base):
    __tablename__ = "ai_suggestion_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    response_summary: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
