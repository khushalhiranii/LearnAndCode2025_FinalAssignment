from __future__ import annotations

from src.api.client import get_client, session


def list_activity_tags() -> list[dict]:
    with get_client() as client:
        resp = client.get(
            "/employee/activity-tags",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def list_allocations() -> list[dict]:
    """Fetch employee's current allocations."""
    with get_client() as client:
        resp = client.get(
            "/employee/allocations",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def list_timesheets() -> list[dict]:
    """Fetch employee's timesheet history."""
    with get_client() as client:
        resp = client.get(
            "/employee/timesheets",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def get_missed_reminder() -> dict:
    with get_client() as client:
        resp = client.get(
            "/employee/timesheets/missed-reminder",
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def submit_timesheet(payload: dict) -> dict:
    """Submit a new timesheet."""
    with get_client() as client:
        resp = client.post(
            "/employee/timesheets",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()
