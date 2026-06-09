"""Manager-specific API calls: dashboard and allocation management."""

from __future__ import annotations

from src.api.client import get_client, session


def get_dashboard() -> dict:
    """GET /manager/dashboard — returns ResourceDashboardResponse."""
    with get_client() as client:
        resp = client.get(
            "/manager/dashboard",
            headers=session.auth_header,
        )
    resp.raise_for_status()
    return resp.json()["data"]


def allocate_employee(
    employee_id: int,
    project_id: int,
    utilization_percent: int,
    from_date: str,
    to_date: str,
) -> dict:
    """POST /manager/allocations — returns AllocationResponse."""
    with get_client() as client:
        resp = client.post(
            "/manager/allocations",
            json={
                "employee_id": employee_id,
                "project_id": project_id,
                "utilization_percent": utilization_percent,
                "from_date": from_date,
                "to_date": to_date,
            },
            headers=session.auth_header,
        )
    resp.raise_for_status()
    return resp.json()["data"]


def list_my_allocations() -> list:
    """GET /manager/allocations — returns all allocations for the manager's team."""
    with get_client() as client:
        resp = client.get(
            "/manager/allocations",
            headers=session.auth_header,
        )
    resp.raise_for_status()
    return resp.json()["data"]


def end_allocation(allocation_id: int, ended_at: str) -> dict:
    """PATCH /manager/allocations/{id}/end — ends an active allocation."""
    with get_client() as client:
        resp = client.patch(
            f"/manager/allocations/{allocation_id}/end",
            json={"ended_at": ended_at},
            headers=session.auth_header,
        )
    resp.raise_for_status()
    return resp.json()["data"]


def list_my_projects() -> list:
    """GET /manager/projects — returns projects managed by the current manager."""
    with get_client() as client:
        resp = client.get(
            "/manager/projects",
            headers=session.auth_header,
        )
    resp.raise_for_status()
    return resp.json()["data"]
