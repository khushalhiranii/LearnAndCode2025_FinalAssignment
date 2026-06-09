"""Unit tests for project and milestone use cases (Sprint 3)."""

import pytest

from src.application.admin.create_project_use_case import CreateProjectUseCase
from src.application.admin.list_projects_use_case import ListProjectsUseCase
from src.application.admin.milestone_use_case import MilestoneUseCase
from src.application.admin.update_project_use_case import UpdateProjectUseCase
from src.application.dtos.project_dtos import (
    AddMilestoneRequest,
    CreateProjectRequest,
    UpdateMilestoneStatusRequest,
    UpdateProjectRequest,
)
from src.domain.enums import MilestoneStatus, ProjectStatus, Role
from src.domain.exceptions import (
    DuplicateProjectNameError,
    InvalidProjectManagerError,
    MilestoneNotFoundError,
    ProjectNotFoundError,
)
from tests.conftest import (
    InMemoryMilestoneRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
    make_admin_user,
    make_milestone,
    make_project,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_manager_user(user_id: int = 2) -> object:
    """Return an active MANAGER user via make_admin_user with role patched."""
    from src.domain.entities.user import User
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return User(
        id=user_id,
        full_name="Alice Manager",
        email=f"alice{user_id}@example.com",
        username=f"alice{user_id}",
        password_hash=b"x",
        role=Role.MANAGER,
        is_active=True,
        force_password_change=False,
        created_at=now,
        updated_at=now,
    )


# ── CreateProject tests ───────────────────────────────────────────────────────


async def test_create_project_returns_response():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    manager = _make_manager_user()
    await user_repo.save(manager)

    use_case = CreateProjectUseCase(project_repo, user_repo)
    req = CreateProjectRequest(name="Alpha", manager_user_id=manager.id)
    result = await use_case.execute(req)

    assert result.id is not None
    assert result.name == "Alpha"
    assert result.completed_story_points == 0
    assert result.status == ProjectStatus.PLANNED


async def test_create_project_raises_duplicate_name():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    manager = _make_manager_user()
    await user_repo.save(manager)
    existing = make_project(name="Alpha", manager_user_id=manager.id)
    await project_repo.save(existing)

    use_case = CreateProjectUseCase(project_repo, user_repo)
    with pytest.raises(DuplicateProjectNameError):
        await use_case.execute(CreateProjectRequest(name="Alpha", manager_user_id=manager.id))


async def test_create_project_invalid_manager_role_raises():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    admin = make_admin_user()  # role=ADMIN, not MANAGER
    await user_repo.save(admin)

    use_case = CreateProjectUseCase(project_repo, user_repo)
    with pytest.raises(InvalidProjectManagerError):
        await use_case.execute(CreateProjectRequest(name="Beta", manager_user_id=admin.id))


async def test_create_project_inactive_manager_raises():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    from src.domain.entities.user import User
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    inactive_manager = User(
        id=5, full_name="Bob", email="bob@x.com", username="bob",
        password_hash=b"x", role=Role.MANAGER, is_active=False,
        force_password_change=False, created_at=now, updated_at=now,
    )
    await user_repo.save(inactive_manager)

    use_case = CreateProjectUseCase(project_repo, user_repo)
    with pytest.raises(InvalidProjectManagerError):
        await use_case.execute(CreateProjectRequest(name="Gamma", manager_user_id=5))


# ── UpdateProject tests ───────────────────────────────────────────────────────


async def test_update_project_partial_update_name():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    manager = _make_manager_user()
    await user_repo.save(manager)
    project = make_project(name="Old Name", manager_user_id=manager.id)
    await project_repo.save(project)

    use_case = UpdateProjectUseCase(project_repo, user_repo)
    result = await use_case.execute(project.id, UpdateProjectRequest(name="New Name"))

    assert result.name == "New Name"
    assert result.manager_user_id == manager.id  # unchanged


async def test_update_project_duplicate_name_raises():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    manager = _make_manager_user()
    await user_repo.save(manager)
    p1 = make_project(project_id=1, name="Taken", manager_user_id=manager.id)
    p2 = make_project(project_id=2, name="Other", manager_user_id=manager.id)
    await project_repo.save(p1)
    await project_repo.save(p2)

    use_case = UpdateProjectUseCase(project_repo, user_repo)
    with pytest.raises(DuplicateProjectNameError):
        await use_case.execute(p2.id, UpdateProjectRequest(name="Taken"))


async def test_update_project_raises_for_unknown():
    project_repo = InMemoryProjectRepository()
    user_repo = InMemoryUserRepository()
    use_case = UpdateProjectUseCase(project_repo, user_repo)
    with pytest.raises(ProjectNotFoundError):
        await use_case.execute(999, UpdateProjectRequest(name="X"))


# ── ListProjects tests ────────────────────────────────────────────────────────


async def test_list_projects_returns_all():
    project_repo = InMemoryProjectRepository()
    await project_repo.save(make_project(project_id=1, name="P1"))
    await project_repo.save(make_project(project_id=2, name="P2"))

    use_case = ListProjectsUseCase(project_repo)
    result = await use_case.execute()

    assert result.total == 2
    assert len(result.items) == 2


async def test_list_projects_filters_by_status():
    project_repo = InMemoryProjectRepository()
    await project_repo.save(make_project(project_id=1, name="P1", status=ProjectStatus.ACTIVE))
    await project_repo.save(make_project(project_id=2, name="P2", status=ProjectStatus.PLANNED))

    use_case = ListProjectsUseCase(project_repo)
    result = await use_case.execute(status=ProjectStatus.ACTIVE)

    assert result.total == 1
    assert result.items[0].name == "P1"


async def test_list_projects_filters_by_manager():
    project_repo = InMemoryProjectRepository()
    await project_repo.save(make_project(project_id=1, name="P1", manager_user_id=10))
    await project_repo.save(make_project(project_id=2, name="P2", manager_user_id=20))

    use_case = ListProjectsUseCase(project_repo)
    result = await use_case.execute(manager_user_id=10)

    assert result.total == 1
    assert result.items[0].manager_user_id == 10


# ── Milestone tests ───────────────────────────────────────────────────────────


async def test_add_milestone_adds_with_pending_status():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    project = make_project()
    await project_repo.save(project)

    use_case = MilestoneUseCase(project_repo, milestone_repo)
    result = await use_case.add_milestone(
        project.id, AddMilestoneRequest(title="M1", story_points=20)
    )

    assert result.status == MilestoneStatus.PENDING
    assert result.story_points == 20
    assert result.project_id == project.id


async def test_add_milestone_raises_for_unknown_project():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    use_case = MilestoneUseCase(project_repo, milestone_repo)
    with pytest.raises(ProjectNotFoundError):
        await use_case.add_milestone(999, AddMilestoneRequest(title="M1"))


async def test_update_milestone_status_to_done_updates_completed_points():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    project = make_project(total_story_points=50)
    await project_repo.save(project)
    milestone = make_milestone(project_id=project.id, story_points=30)
    await milestone_repo.save(milestone)

    use_case = MilestoneUseCase(project_repo, milestone_repo)
    result = await use_case.update_milestone_status(
        milestone.id, UpdateMilestoneStatusRequest(status=MilestoneStatus.DONE)
    )

    assert result.status == MilestoneStatus.DONE
    updated_project = await project_repo.find_by_id(project.id)
    assert updated_project.completed_story_points == 30


async def test_update_milestone_status_from_done_back_reduces_completed_points():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    project = make_project(total_story_points=50, completed_story_points=30)
    await project_repo.save(project)
    milestone = make_milestone(
        project_id=project.id, story_points=30, status=MilestoneStatus.DONE
    )
    await milestone_repo.save(milestone)

    use_case = MilestoneUseCase(project_repo, milestone_repo)
    await use_case.update_milestone_status(
        milestone.id, UpdateMilestoneStatusRequest(status=MilestoneStatus.IN_PROGRESS)
    )

    updated_project = await project_repo.find_by_id(project.id)
    assert updated_project.completed_story_points == 0


async def test_update_milestone_status_raises_for_unknown():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    use_case = MilestoneUseCase(project_repo, milestone_repo)
    with pytest.raises(MilestoneNotFoundError):
        await use_case.update_milestone_status(
            999, UpdateMilestoneStatusRequest(status=MilestoneStatus.DONE)
        )


async def test_list_milestones_returns_all_for_project():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    project = make_project()
    await project_repo.save(project)
    await milestone_repo.save(make_milestone(milestone_id=1, project_id=project.id, title="M1"))
    await milestone_repo.save(make_milestone(milestone_id=2, project_id=project.id, title="M2"))

    use_case = MilestoneUseCase(project_repo, milestone_repo)
    result = await use_case.list_milestones(project.id)

    assert len(result) == 2


async def test_list_milestones_raises_for_unknown_project():
    project_repo = InMemoryProjectRepository()
    milestone_repo = InMemoryMilestoneRepository()
    use_case = MilestoneUseCase(project_repo, milestone_repo)
    with pytest.raises(ProjectNotFoundError):
        await use_case.list_milestones(999)
