import pytest
from httpx import AsyncClient

from tests.integration.api.helpers import auth_headers, login_and_get_token


@pytest.mark.asyncio
async def test_manager_flow_end_to_end(seeded_admin_client: AsyncClient):
    """
    Manager flow (V6):
    Admin sets up manager, employee, project → manager allocates, views dashboard,
    rejects over-allocation, ends allocation.
    """
    client = seeded_admin_client

    admin_token = await login_and_get_token(
        client, "admin", "Admin@1234", new_password="NewAdminPassword!@1"
    )
    admin_headers = auth_headers(admin_token)

    resp = await client.post(
        "/admin/users",
        json={
            "username": "test_manager",
            "email": "manager@example.com",
            "full_name": "Test Manager",
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
            "username": "test_employee",
            "email": "emp@example.com",
            "full_name": "Test Employee",
            "role": "EMPLOYEE",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
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
            "name": "E2E Test Project",
            "description": "Integration testing project",
            "manager_user_id": manager_id,
            "status": "PLANNED",
            "total_story_points": 100,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    project_id = resp.json()["id"]

    manager_token = await login_and_get_token(
        client, "test_manager", manager_pwd, new_password="NewManager@123"
    )
    manager_headers = auth_headers(manager_token)

    resp = await client.get("/manager/dashboard", headers=manager_headers)
    assert resp.status_code == 200
    dashboard = resp.json()
    assert dashboard["total_team_size"] == 1
    assert dashboard["bench_count"] == 1
    assert dashboard["team"][0]["resource_profile_id"] == emp_id
    assert dashboard["team"][0]["availability_label"] == "BENCH"

    resp = await client.post(
        "/manager/allocations",
        json={
            "resource_profile_id": emp_id,
            "project_id": project_id,
            "utilization_percent": 100,
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        },
        headers=manager_headers,
    )
    assert resp.status_code == 201, resp.text
    allocation_id = resp.json()["id"]

    resp = await client.post(
        "/manager/allocations",
        json={
            "resource_profile_id": emp_id,
            "project_id": project_id,
            "utilization_percent": 20,
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
        },
        headers=manager_headers,
    )
    assert resp.status_code == 409
    assert "exceed 100% utilization" in resp.json()["error"]["message"]

    resp = await client.get("/manager/dashboard", headers=manager_headers)
    dashboard = resp.json()
    assert dashboard["bench_count"] == 0
    assert dashboard["allocated_count"] == 1
    assert dashboard["team"][0]["availability_label"] == "ALLOCATED"
    assert dashboard["team"][0]["total_utilization_percent"] == 100

    resp = await client.get("/manager/projects?page=1&page_size=20", headers=manager_headers)
    assert resp.status_code == 200
    projects = resp.json()["items"]
    assert len(projects) == 1
    assert projects[0]["id"] == project_id

    resp = await client.get("/manager/timesheets?week_start=2026-01-05", headers=manager_headers)
    assert resp.status_code == 200
    timesheets = resp.json()["items"]
    assert not any(t["status"] == "SUBMITTED" for t in timesheets)

    resp = await client.patch(
        f"/manager/allocations/{allocation_id}/end",
        json={"ended_at": "2026-06-01"},
        headers=manager_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ENDED"

    resp = await client.get("/manager/dashboard", headers=manager_headers)
    dashboard = resp.json()
    assert dashboard["bench_count"] == 1
    assert dashboard["allocated_count"] == 0
