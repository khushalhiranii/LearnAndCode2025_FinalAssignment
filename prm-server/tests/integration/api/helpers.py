"""Shared helpers for V6 API integration tests."""

from httpx import AsyncClient


async def login_and_get_token(
    client: AsyncClient,
    username: str,
    password: str,
    new_password: str | None = None,
) -> str:
    """Login; if password change is required, complete it and return access token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    if data.get("status") == "PASSWORD_CHANGE_REQUIRED":
        temp_token = data["temp_token"]
        assert new_password is not None, "new_password required for first login"
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"new_password": new_password, "confirm_password": new_password},
            headers={"Authorization": f"Bearer {temp_token}"},
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    return data["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
