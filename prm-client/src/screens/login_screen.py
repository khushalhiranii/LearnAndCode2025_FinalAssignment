"""Login screen.

Entry point for all users. Handles both normal login and the forced
password-change flow (temp token → change_password_screen).
"""

from __future__ import annotations

import httpx
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from src.api.auth_api import login
from src.api.client import session
from src.models.response_models import PasswordChangeRequiredResponse
from src.utils.display import console, print_error, print_header, print_success


def show() -> bool:
    """
    Display the login form.

    Returns True if the user is now authenticated (access token stored in
    the session singleton), False if login ultimately failed.
    """
    print_header("PRM Tool — Login")

    while True:
        username = prompt(HTML("<b>Username:</b> ")).strip()
        password = prompt(HTML("<b>Password:</b> "), is_password=True).strip()

        if not username or not password:
            print_error("Username and password are required.")
            continue

        try:
            result = login(username, password)
        except httpx.HTTPStatusError as exc:
            data = exc.response.json()
            print_error(data.get("error", {}).get("message", "Login failed."))
            continue
        except Exception as exc:
            print_error(f"Connection error: {exc}")
            continue

        if isinstance(result, PasswordChangeRequiredResponse):
            # Lazy import to avoid circular imports
            from src.screens import change_password_screen  # noqa: PLC0415

            return change_password_screen.show(result.temp_token)

        # Normal login
        session.set_tokens(result.access_token, result.role, result.full_name)
        print_success(f"Welcome back, {result.full_name}!")
        return True
