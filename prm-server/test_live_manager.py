import asyncio
from httpx import AsyncClient

async def run_live_test():
    client = AsyncClient(base_url="http://localhost:8000")
    print("Connecting to live backend...")

    # 1. Login as Admin
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@1234"})
    assert resp.status_code == 200, f"Failed: {resp.text}"
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("1. Admin Login Success")

    import time
    unique_id = int(time.time())

    # 2. Create a Manager
    resp = await client.post(
        "/admin/users",
        json={"username": f"mgr_{unique_id}", "email": f"mgr_{unique_id}@test.local", "full_name": "Test Manager", "role": "MANAGER"},
        headers=admin_headers
    )
    assert resp.status_code == 201, f"Failed: {resp.text}"
    manager_data = resp.json()["data"]
    manager_id = manager_data["id"]
    manager_pwd = manager_data["temp_password"]
    print(f"2. Manager User Created ({manager_id})")

    # 3. Create an Employee
    resp = await client.post(
        "/admin/users",
        json={"username": f"emp_{unique_id}", "email": f"emp_{unique_id}@test.local", "full_name": "Test Employee", "role": "RESOURCE"},
        headers=admin_headers
    )
    assert resp.status_code == 201, f"Failed: {resp.text}"
    emp_user_id = resp.json()["data"]["id"]
    
    resp = await client.get("/admin/employees", headers=admin_headers)
    assert resp.status_code == 200
    employees = resp.json()["data"]["items"]
    emp_profile = next(e for e in employees if e["user_id"] == emp_user_id)
    emp_id = emp_profile["id"]
    print(f"3. Employee Created ({emp_id})")

    # 4. Admin assigns Manager to Employee
    resp = await client.post(
        f"/admin/employees/{emp_id}/assign-manager",
        json={"manager_user_id": manager_id},
        headers=admin_headers
    )
    assert resp.status_code == 200, f"Failed: {resp.text}"
    print("4. Assigned manager to employee")

    # 5. Admin creates a Project
    resp = await client.post(
        "/admin/projects",
        json={
            "name": f"Project {unique_id}",
            "description": "Integration testing project",
            "manager_user_id": manager_id,
            "status": "PLANNED",
            "total_story_points": 100
        },
        headers=admin_headers
    )
    assert resp.status_code == 201, f"Failed: {resp.text}"
    project_id = resp.json()["data"]["id"]
    print("5. Created Project")

    # 6. Manager logs in (and sets new password)
    resp = await client.post("/api/v1/auth/login", json={"username": f"mgr_{unique_id}", "password": manager_pwd})
    assert resp.status_code == 403, f"Failed: {resp.text}"
    temp_token = resp.json()["error"]["temp_token"]

    resp = await client.post("/api/v1/auth/change-password", json={"temp_token": temp_token, "new_password": "NewManager@123", "confirm_password": "NewManager@123"}, headers={"Authorization": f"Bearer {temp_token}"})
    assert resp.status_code == 200, f"Failed: {resp.text}"
    manager_token = resp.json()["data"]["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    print("6. Manager logged in and reset password")

    # 7. Manager views Dashboard
    resp = await client.get("/manager/dashboard", headers=manager_headers)
    assert resp.status_code == 200, f"Failed: {resp.text}"
    dashboard = resp.json()
    assert dashboard["total_team_size"] == 1
    assert dashboard["bench_count"] == 1
    assert dashboard["team"][0]["employee_id"] == emp_id
    assert dashboard["team"][0]["availability_label"] == "BENCH"
    print("7. Dashboard verified (employee on BENCH)")

    # 8. Manager creates an allocation (100%)
    resp = await client.post(
        "/manager/allocations",
        json={
            "employee_id": emp_id,
            "project_id": project_id,
            "utilization_percent": 100,
            "from_date": "2026-01-01",
            "to_date": "2026-12-31"
        },
        headers=manager_headers
    )
    assert resp.status_code == 201, f"Failed: {resp.text}"
    allocation_id = resp.json()["id"]
    print("8. Allocated 100%")

    # 9. Manager attempts over-allocation edge case (should fail)
    resp = await client.post(
        "/manager/allocations",
        json={
            "employee_id": emp_id,
            "project_id": project_id,
            "utilization_percent": 20, 
            "from_date": "2026-01-01",
            "to_date": "2026-12-31"
        },
        headers=manager_headers
    )
    assert resp.status_code == 400, "Should have failed with 400"
    assert "would exceed maximum 100%" in resp.json()["error"]["message"]
    print("9. Edge Case Caught: Over-allocation gracefully prevented with 400 error")

    # 10. Manager views Dashboard (employee should be allocated)
    resp = await client.get("/manager/dashboard", headers=manager_headers)
    assert resp.status_code == 200
    dashboard = resp.json()
    assert dashboard["bench_count"] == 0
    assert dashboard["allocated_count"] == 1
    assert dashboard["team"][0]["availability_label"] == "ALLOCATED"
    assert dashboard["team"][0]["total_utilization_percent"] == 100
    print("10. Dashboard verified (employee ALLOCATED)")

    # 11. Manager views their projects
    resp = await client.get("/manager/projects?page=1&page_size=20", headers=manager_headers)
    assert resp.status_code == 200
    projects = resp.json()["data"]["items"]
    assert len(projects) == 1
    assert projects[0]["id"] == project_id
    print("11. Manager projects fetched")

    # 12. Manager views team timesheets
    resp = await client.get("/manager/timesheets?week_start=2026-01-05", headers=manager_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 0
    print("12. Manager timesheets fetched (empty as expected)")

    # 13. Manager ends the allocation
    resp = await client.patch(
        f"/manager/allocations/{allocation_id}/end",
        json={"ended_at": "2026-06-01"},
        headers=manager_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ENDED"
    print("13. Allocation ended successfully")

    # 14. Manager Dashboard should reflect bench status again
    resp = await client.get("/manager/dashboard", headers=manager_headers)
    assert resp.status_code == 200
    dashboard = resp.json()
    assert dashboard["bench_count"] == 1
    assert dashboard["allocated_count"] == 0
    print("14. Final Dashboard Verification: Employee back on BENCH.")

    print("\n[SUCCESS] Manager E2E flow fully validated against the live server!")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(run_live_test())
