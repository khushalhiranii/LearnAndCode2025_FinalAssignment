"""Rebuild resource_hierarchy closure rows when manager assignment changes."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.resource_hierarchy_model import ResourceHierarchyModel


class ResourceHierarchyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def rebuild_for_profile(self, resource_profile_id: int, manager_user_id: int | None) -> None:
        """Delete old ancestor rows for this descendant and insert new closure rows."""
        await self._session.execute(
            delete(ResourceHierarchyModel).where(
                ResourceHierarchyModel.descendant_id == resource_profile_id
            )
        )

        # Self row
        self._session.add(
            ResourceHierarchyModel(
                ancestor_id=resource_profile_id,
                descendant_id=resource_profile_id,
                depth=0,
            )
        )

        if manager_user_id is None:
            await self._session.flush()
            return

        from src.infrastructure.database.models.employee_model import ResourceProfileModel

        manager_profile = (
            await self._session.execute(
                select(ResourceProfileModel).where(ResourceProfileModel.user_id == manager_user_id)
            )
        ).scalar_one_or_none()
        if manager_profile is None:
            await self._session.flush()
            return

        manager_profile_id = manager_profile.id
        ancestor_rows = (
            await self._session.execute(
                select(ResourceHierarchyModel).where(
                    ResourceHierarchyModel.descendant_id == manager_profile_id
                )
            )
        ).scalars().all()

        for row in ancestor_rows:
            self._session.add(
                ResourceHierarchyModel(
                    ancestor_id=row.ancestor_id,
                    descendant_id=resource_profile_id,
                    depth=row.depth + 1,
                )
            )
        await self._session.flush()

    async def ensure_self_row(self, resource_profile_id: int) -> None:
        existing = (
            await self._session.execute(
                select(ResourceHierarchyModel).where(
                    ResourceHierarchyModel.ancestor_id == resource_profile_id,
                    ResourceHierarchyModel.descendant_id == resource_profile_id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            self._session.add(
                ResourceHierarchyModel(
                    ancestor_id=resource_profile_id,
                    descendant_id=resource_profile_id,
                    depth=0,
                )
            )
            await self._session.flush()
