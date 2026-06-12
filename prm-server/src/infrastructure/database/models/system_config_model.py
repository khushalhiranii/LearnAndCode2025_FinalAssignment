from sqlalchemy import BigInteger, String, Text, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base


class SystemConfigModel(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by_user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
