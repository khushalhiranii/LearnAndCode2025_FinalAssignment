"""Change-password screen.

Displayed immediately after login when force_password_change=True.
Receives the temp_token from the login screen.
"""

from __future__ import annotations

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from src.api.auth_api import change_password
from src.api.client import session
from src.utils.display import console, print_error, print_success, print_warning
from src.utils.validation import validate_password_strength


def show(temp_token: str) -> bool:
    """
    Show the change-password form.

    Returns True if the password was changed successfully (user is now
    authenticated with a full access token), False if the user aborted.
    """
    console.rule("[bold yellow]Password Change Required[/bold yellow]")
    console.print("You must set a new password before continuing.\n")

    while True:
        new_password = prompt(HTML("<b>New password:</b> "), is_password=True).strip()
        if not new_password:
            print_warning("Cancelled.")
            return False

        errors = validate_password_strength(new_password)
        if errors:
            for err in errors:
                print_error(err)
            continue

        confirm_password = prompt(
            HTML("<b>Confirm new password:</b> "), is_password=True
        ).strip()

        if new_password != confirm_password:
            print_error("Passwords do not match. Please try again.")
            continue

        try:
            result = change_password(temp_token, new_password, confirm_password)
            session.set_tokens(result.access_token, result.role, result.full_name)
            print_success(f"Password changed. Welcome, {result.full_name}!")
            return True
        except Exception as exc:
            print_error(f"Failed to change password: {exc}")
            return False
