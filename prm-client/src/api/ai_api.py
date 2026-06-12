"""AI API calls for manager."""

from __future__ import annotations

from src.api.client import get_client, session


def skill_match(query: str, project_id: int | None = None, hours_per_week: float | None = None) -> dict:
    payload: dict = {"query": query}
    if project_id is not None:
        payload["project_id"] = project_id
    if hours_per_week is not None:
        payload["hours_per_week"] = hours_per_week
    with get_client() as client:
        resp = client.post(
            "/manager/ai/skill-match",
            json=payload,
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()


def risk_summary(project_id: int) -> dict:
    with get_client() as client:
        resp = client.post(
            "/manager/ai/risk-summary",
            json={"project_id": project_id},
            headers={"Authorization": f"Bearer {session.access_token}"},
        )
    resp.raise_for_status()
    return resp.json()
