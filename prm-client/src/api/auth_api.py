"""Auth-related API calls."""

from __future__ import annotations

import httpx

from src.api.client import get_client
from src.models.response_models import (
    ChangePasswordResponse,
    LoginResponse,
    PasswordChangeRequiredResponse,
)


def login(
    username: str, password: str
) -> LoginResponse | PasswordChangeRequiredResponse:
    """
    POST /api/v1/auth/login

    Returns either LoginResponse (normal login) or PasswordChangeRequiredResponse
    (force_password_change=True).

    Raises httpx.HTTPStatusError on 4xx/5xx responses.
    """
    with get_client() as client:
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
    resp.raise_for_status()
    data = resp.json()
    if "temp_token" in data:
        return PasswordChangeRequiredResponse(**data)
    return LoginResponse(**data)


def change_password(
    temp_token: str, new_password: str, confirm_password: str
) -> ChangePasswordResponse:
    """
    POST /api/v1/auth/change-password

    Requires the temp_token issued by login when force_password_change=True.
    Raises httpx.HTTPStatusError on 4xx/5xx responses.
    """
    with get_client() as client:
        resp = client.post(
            "/api/v1/auth/change-password",
            json={"new_password": new_password, "confirm_password": confirm_password},
            headers={"Authorization": f"Bearer {temp_token}"},
        )
    resp.raise_for_status()
    return ChangePasswordResponse(**resp.json())
