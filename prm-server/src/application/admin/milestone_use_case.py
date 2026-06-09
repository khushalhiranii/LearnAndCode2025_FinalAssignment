from datetime import datetime, timezone

from src.application.dtos.project_dtos import (
    AddMilestoneRequest,
    MilestoneResponse,
    UpdateMilestoneStatusRequest,
)
from src.domain.entities.milestone import Milestone
from src.domain.exceptions import MilestoneNotFoundError, ProjectNotFoundError
from src.domain.ports.repositories import IMilestoneRepository, IProjectRepository


class MilestoneUseCase:

    def __init__(
        self,
        project_repo: IProjectRepository,
        milestone_repo: IMilestoneRepository,
    ) -> None:
        self._projects = project_repo
        self._milestones = milestone_repo

    async def add_milestone(
        self, project_id: int, request: AddMilestoneRequest
    ) -> MilestoneResponse:
        project = await self._projects.find_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found.")

        now = datetime.now(timezone.utc)
        from src.domain.enums import MilestoneStatus
        milestone = Milestone(
            id=None,
            project_id=project_id,
            title=request.title,
            description=request.description,
            due_date=request.due_date,
            status=MilestoneStatus.PENDING,
            story_points=request.story_points,
            created_at=now,
            updated_at=now,
        )
        saved = await self._milestones.save(milestone)
        return _to_response(saved)

    async def update_milestone_status(
        self, milestone_id: int, request: UpdateMilestoneStatusRequest
    ) -> MilestoneResponse:
        milestone = await self._milestones.find_by_id(milestone_id)
        if milestone is None:
            raise MilestoneNotFoundError(f"Milestone {milestone_id} not found.")

        await self._milestones.update_status(milestone_id, request.status)

        # Recompute and persist completed_story_points for the parent project
        done_points = await self._milestones.sum_done_story_points(milestone.project_id)
        await self._projects.update_completed_points(milestone.project_id, done_points)

        # Return updated view
        updated = await self._milestones.find_by_id(milestone_id)
        return _to_response(updated)

    async def list_milestones(self, project_id: int) -> list[MilestoneResponse]:
        project = await self._projects.find_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found.")
        milestones = await self._milestones.find_by_project(project_id)
        return [_to_response(m) for m in milestones]


def _to_response(milestone: Milestone) -> MilestoneResponse:
    return MilestoneResponse(
        id=milestone.id,
        project_id=milestone.project_id,
        title=milestone.title,
        description=milestone.description,
        due_date=milestone.due_date,
        status=milestone.status,
        story_points=milestone.story_points,
        created_at=milestone.created_at,
        updated_at=milestone.updated_at,
    )
