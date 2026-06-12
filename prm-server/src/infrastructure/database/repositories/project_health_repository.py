import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.project_health import AISuggestionAudit, ProjectHealthSnapshot
from src.domain.enums import ProjectHealthStatus
from src.domain.ports.repositories import IAISuggestionAuditRepository, IProjectHealthRepository
from src.infrastructure.database.models.project_health_model import (
    AISuggestionAuditModel,
    ProjectHealthSnapshotModel,
)


class SQLAlchemyProjectHealthRepository(IProjectHealthRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_snapshot(self, snapshot: ProjectHealthSnapshot) -> ProjectHealthSnapshot:
        model = ProjectHealthSnapshotModel(
            project_id=snapshot.project_id,
            health_status=snapshot.health_status.value,
            risk_flags_json=snapshot.risk_flags_json,
            computed_at=snapshot.computed_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _snapshot_to_entity(model)

    async def find_latest_by_project(self, project_id: int) -> ProjectHealthSnapshot | None:
        result = await self._session.execute(
            select(ProjectHealthSnapshotModel)
            .where(ProjectHealthSnapshotModel.project_id == project_id)
            .order_by(ProjectHealthSnapshotModel.computed_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _snapshot_to_entity(model) if model else None

    async def find_latest_by_projects(
        self, project_ids: list[int]
    ) -> dict[int, ProjectHealthSnapshot]:
        if not project_ids:
            return {}
        latest: dict[int, ProjectHealthSnapshot] = {}
        for pid in project_ids:
            snap = await self.find_latest_by_project(pid)
            if snap:
                latest[pid] = snap
        return latest


class SQLAlchemyAISuggestionAuditRepository(IAISuggestionAuditRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, audit: AISuggestionAudit) -> AISuggestionAudit:
        model = AISuggestionAuditModel(
            request_type=audit.request_type,
            subject_id=audit.subject_id,
            input_summary=audit.input_summary,
            response_summary=audit.response_summary,
            provider=audit.provider,
            created_at=audit.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        audit.id = model.id
        return audit


def _snapshot_to_entity(model: ProjectHealthSnapshotModel) -> ProjectHealthSnapshot:
    return ProjectHealthSnapshot(
        id=model.id,
        project_id=model.project_id,
        health_status=ProjectHealthStatus(model.health_status),
        risk_flags_json=model.risk_flags_json,
        computed_at=model.computed_at,
    )


def parse_risk_flags(risk_flags_json: str | None) -> list[str]:
    if not risk_flags_json:
        return []
    try:
        data = json.loads(risk_flags_json)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
