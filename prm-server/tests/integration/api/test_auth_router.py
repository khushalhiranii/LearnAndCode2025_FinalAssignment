import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
class TestLoginEndpoint:

    async def test_valid_credentials_return_password_change_required(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PASSWORD_CHANGE_REQUIRED"
        assert "temp_token" in data

    async def test_wrong_password_returns_401(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "WrongPass@1"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_unknown_user_returns_401(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "Any@Pass1"},
        )
        assert resp.status_code == 401

    async def test_missing_password_returns_422(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestChangePasswordEndpoint:

    async def test_change_password_success_returns_200(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        login_resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@1234"},
        )
        temp_token = login_resp.json()["temp_token"]

        resp = await seeded_admin_client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "NewAdmin@99", "confirm_password": "NewAdmin@99"},
            headers={"Authorization": f"Bearer {temp_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "ADMIN"

        # VERIFICATION: Logging in again with the new password should succeed
        # and NOT require another password change
        second_login_resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "NewAdmin@99"},
        )
        assert second_login_resp.status_code == 200
        second_login_data = second_login_resp.json()
        assert "access_token" in second_login_data
        assert "temp_token" not in second_login_data
        assert second_login_data.get("status") != "PASSWORD_CHANGE_REQUIRED"

    async def test_change_password_with_access_token_rejected(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        """An access token (not a temp token) must be rejected at this endpoint."""
        login_resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@1234"},
        )
        temp_token = login_resp.json()["temp_token"]
        change_resp = await seeded_admin_client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "NewAdmin@99", "confirm_password": "NewAdmin@99"},
            headers={"Authorization": f"Bearer {temp_token}"},
        )
        access_token = change_resp.json()["access_token"]

        # Attempt to use the access token at the change-password endpoint — must fail
        resp = await seeded_admin_client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "Another@99", "confirm_password": "Another@99"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code in (401, 403)

    async def test_weak_password_returns_422(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        login_resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@1234"},
        )
        temp_token = login_resp.json()["temp_token"]
        resp = await seeded_admin_client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "weakpass", "confirm_password": "weakpass"},
            headers={"Authorization": f"Bearer {temp_token}"},
        )
        assert resp.status_code == 422

    async def test_mismatched_passwords_returns_422(
        self, seeded_admin_client: AsyncClient
    ) -> None:
        login_resp = await seeded_admin_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "Admin@1234"},
        )
        temp_token = login_resp.json()["temp_token"]
        resp = await seeded_admin_client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "Valid@Pass1", "confirm_password": "Different@1"},
            headers={"Authorization": f"Bearer {temp_token}"},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestHealthEndpoint:

    async def test_liveness_returns_200(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
