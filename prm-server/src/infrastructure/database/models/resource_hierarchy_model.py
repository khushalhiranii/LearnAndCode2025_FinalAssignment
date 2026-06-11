from sqlalchemy import BigInteger, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base


class ResourceHierarchyModel(Base):
    __tablename__ = "resource_hierarchy"

    ancestor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resource_profiles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    descendant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resource_profiles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    depth: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="0=self, 1=direct report, n=nth level"
    )
