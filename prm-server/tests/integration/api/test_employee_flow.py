import pytest
from httpx import AsyncClient

from tests.integration.api.helpers import auth_headers, login_and_get_token


@pytest.mark.asyncio
async def test_employee_allocations_and_timesheet_flow(seeded_admin_client: AsyncClient):
    """
    Employee flow (V6):
    1. Admin creates manager + employee, project, allocation.
    2. Employee submits a timesheet for an allocated week.
    3. Validation rejects future weeks and duplicate submissions.
    """
    client = seeded_admin_client

    admin_token = await login_and_get_token(
        client, "admin", "Admin@1234", new_password="NewAdminPassword!@1"
    )
    admin_headers = auth_headers(admin_token)

    resp = await client.post(
        "/admin/users",
        json={
            "username": "test_manager_empflow",
            "email": "mgr_empflow@example.com",
            "full_name": "Flow Manager",
            "role": "MANAGER",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    manager_id = resp.json()["data"]["id"]
    manager_pwd = resp.json()["data"]["temp_password"]

    resp = await client.post(
        "/admin/users",
        json={
            "username": "test_employee_flow",
            "email": "empflow@example.com",
            "full_name": "Test Employee",
            "role": "EMPLOYEE",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    emp_pwd = resp.json()["data"]["temp_password"]
    emp_user_id = resp.json()["data"]["id"]

    resp = await client.get("/admin/employees", headers=admin_headers)
    emp_profile = next(e for e in resp.json()["data"]["items"] if e["user_id"] == emp_user_id)
    emp_id = emp_profile["id"]

    await client.post(
        f"/admin/employees/{emp_id}/assign-manager",
        json={"manager_user_id": manager_id},
        headers=admin_headers,
    )

    resp = await client.post(
        "/admin/projects",
        json={
            "name": "Employee Flow Project",
            "description": "Integration test project",
            "manager_user_id": manager_id,
            "status": "ACTIVE",
            "total_story_points": 100,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    project_id = resp.json()["id"]

    manager_token = await login_and_get_token(
        client, "test_manager_empflow", manager_pwd, new_password="NewManager@123"
    )
    await client.post(
        "/manager/allocations",
        json={
            "resource_profile_id": emp_id,
            "project_id": project_id,
            "utilization_percent": 100,
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        },
        headers=auth_headers(manager_token),
    )

    employee_token = await login_and_get_token(
        client, "test_employee_flow", emp_pwd, new_password="NewEmployee@123"
    )
    employee_headers = auth_headers(employee_token)

    resp = await client.get("/employee/allocations", headers=employee_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp = await client.get("/employee/activity-tags", headers=employee_headers)
    assert resp.status_code == 200
    tags = resp.json()
    assert len(tags) >= 1
    tag_id = tags[0]["id"]

    week_start = "2026-06-09"
    submit_payload = {
        "week_start_date": week_start,
        "entries": [
            {
                "project_id": project_id,
                "hours_worked": 40.0,
                "tags": [{"activity_tag_id": tag_id, "custom_tag_text": None}],
            }
        ],
    }
    resp = await client.post(
        "/employee/timesheets",
        json=submit_payload,
        headers=employee_headers,
    )
    assert resp.status_code == 201, resp.text
    ts = resp.json()
    assert ts["total_hours"] == 40.0
    assert ts["status"] == "SUBMITTED"

    resp = await client.get("/employee/timesheets", headers=employee_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert any(h["id"] == ts["id"] for h in history)

    resp = await client.post(
        "/employee/timesheets",
        json={
            "week_start_date": "2099-01-05",
            "entries": [
                {
                    "project_id": project_id,
                    "hours_worked": 10.0,
                    "tags": [{"activity_tag_id": tag_id}],
                }
            ],
        },
        headers=employee_headers,
    )
    assert resp.status_code == 422
    assert "future weeks" in resp.json()["error"]["message"].lower()

    resp = await client.post(
        "/employee/timesheets",
        json=submit_payload,
        headers=employee_headers,
    )
    assert resp.status_code == 409
    assert "already been submitted" in resp.json()["error"]["message"]
