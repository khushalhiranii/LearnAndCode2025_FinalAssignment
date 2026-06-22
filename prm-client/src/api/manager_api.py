from __future__ import annotations

from src.api.client import get_client, session

def get_dashboard() -> dict:
    """Fetch manager's resource dashboard."""
    with get_client() as client:
        resp = client.get(
            "/manager/dashboard",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def allocate_employee(employee_id: int, project_id: int, utilization_percent: int, from_date: str, to_date: str) -> dict:
    """Create a new allocation."""
    payload = {
        "resource_profile_id": employee_id,
        "project_id": project_id,
        "utilization_percent": utilization_percent,
        "from_date": from_date,
        "to_date": to_date
    }
    with get_client() as client:
        resp = client.post(
            "/manager/allocations",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def end_allocation(allocation_id: int, ended_at: str) -> dict:
    """End an active allocation."""
    payload = {
        "ended_at": ended_at
    }
    with get_client() as client:
        resp = client.patch(
            f"/manager/allocations/{allocation_id}/end",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def list_projects(page: int = 1, page_size: int = 20) -> dict:
    """Fetch manager's active projects."""
    with get_client() as client:
        resp = client.get(
            "/manager/projects",
            params={"page": page, "page_size": page_size},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def get_project_detail(project_id: int) -> dict:
    with get_client() as client:
        resp = client.get(
            f"/manager/projects/{project_id}",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def list_timesheets(week_start: str | None = None) -> dict:
    """Fetch timesheets submitted by manager's team."""
    params = {}
    if week_start:
        params["week_start"] = week_start
    with get_client() as client:
        resp = client.get(
            "/manager/timesheets",
            params=params,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def get_timesheet_detail(resource_profile_id: int, week_start: str) -> dict:
    with get_client() as client:
        resp = client.get(
            "/manager/timesheets/detail",
            params={
                "resource_profile_id": resource_profile_id,
                "week_start": week_start,
            },
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def restore_timesheet_access(employee_id: int) -> dict:
    with get_client() as client:
        resp = client.post(
            f"/manager/employees/{employee_id}/restore-timesheet-access",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()
