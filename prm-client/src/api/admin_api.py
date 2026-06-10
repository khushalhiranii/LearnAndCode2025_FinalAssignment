"""Admin-specific API calls: user and employee management."""

from __future__ import annotations

from src.api.client import get_client, session


def create_user(
    username: str,
    email: str,
    full_name: str,
    role: str,
) -> dict:
    """POST /admin/users — returns full response dict including temp_password."""
    with get_client() as client:
        resp = client.post(
            "/admin/users",
            json={"username": username, "email": email, "full_name": full_name, "role": role},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def list_users(
    role: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """GET /admin/users — returns paginated user list."""
    params: dict = {"page": page, "page_size": page_size}
    if role is not None:
        params["role"] = role
    if is_active is not None:
        params["is_active"] = str(is_active).lower()

    with get_client() as client:
        resp = client.get(
            "/admin/users",
            params=params,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def deactivate_user(user_id: int) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/admin/users/{user_id}/deactivate",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def reactivate_user(user_id: int) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/admin/users/{user_id}/reactivate",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def reset_password(user_id: int) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/admin/users/{user_id}/reset-password",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def list_employees(
    is_active: bool | None = None,
    manager_user_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    params: dict = {"page": page, "page_size": page_size}
    if is_active is not None:
        params["is_active"] = str(is_active).lower()
    if manager_user_id is not None:
        params["manager_user_id"] = manager_user_id

    with get_client() as client:
        resp = client.get(
            "/admin/employees",
            params=params,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def update_employee(
    employee_id: int,
    department: str | None = None,
    designation: str | None = None,
    date_of_joining: str | None = None,
) -> dict:
    payload = {}
    if department is not None:
        payload["department"] = department
    if designation is not None:
        payload["designation"] = designation
    if date_of_joining is not None:
        payload["date_of_joining"] = date_of_joining

    with get_client() as client:
        resp = client.patch(
            f"/admin/employees/{employee_id}",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def assign_manager(employee_id: int, manager_user_id: int) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/admin/employees/{employee_id}/assign-manager",
            json={"manager_user_id": manager_user_id},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def list_skills() -> list:
    with get_client() as client:
        resp = client.get(
            "/admin/skills",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def create_skill(name: str, category: str) -> dict:
    with get_client() as client:
        resp = client.post(
            "/admin/skills",
            json={"name": name, "category": category},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def list_employee_skills(employee_id: int) -> list:
    with get_client() as client:
        resp = client.get(
            f"/admin/employees/{employee_id}/skills",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def add_employee_skill(
    employee_id: int, skill_id: int, proficiency: str
) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/admin/employees/{employee_id}/skills",
            json={"skill_id": skill_id, "proficiency": proficiency},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["data"]


def remove_employee_skill(employee_id: int, skill_id: int) -> None:
    with get_client() as client:
        resp = client.delete(
            f"/admin/employees/{employee_id}/skills/{skill_id}",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()


# ── Project & Milestone API calls ─────────────────────────────────────────────


def list_projects(status: str | None = None, manager_user_id: int | None = None) -> dict:
    params: dict = {}
    if status:
        params["status"] = status
    if manager_user_id:
        params["manager_user_id"] = manager_user_id
    with get_client() as client:
        resp = client.get(
            "/admin/projects",
            params=params,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def create_project(payload: dict) -> dict:
    with get_client() as client:
        resp = client.post(
            "/admin/projects",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def get_project(project_id: int) -> dict:
    with get_client() as client:
        resp = client.get(
            f"/admin/projects/{project_id}",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def update_project(project_id: int, payload: dict) -> dict:
    with get_client() as client:
        resp = client.patch(
            f"/admin/projects/{project_id}",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def list_milestones(project_id: int) -> list:
    with get_client() as client:
        resp = client.get(
            f"/admin/projects/{project_id}/milestones",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def add_milestone(project_id: int, payload: dict) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/admin/projects/{project_id}/milestones",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def update_milestone_status(project_id: int, milestone_id: int, status: str) -> dict:
    with get_client() as client:
        resp = client.patch(
            f"/admin/projects/{project_id}/milestones/{milestone_id}/status",
            json={"status": status},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


# ── Allocation API calls (admin) ───────────────────────────────────────────────


def list_all_allocations(
    employee_id: int | None = None,
    project_id: int | None = None,
) -> list:
    """GET /admin/allocations — returns all allocations, optionally filtered."""
    params: dict = {}
    if employee_id is not None:
        params["employee_id"] = employee_id
    if project_id is not None:
        params["project_id"] = project_id
    with get_client() as client:
        resp = client.get(
            "/admin/allocations",
            params=params,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()
