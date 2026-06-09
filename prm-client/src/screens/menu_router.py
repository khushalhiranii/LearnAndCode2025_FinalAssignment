"""Menu router — dispatches to the correct role-specific main menu."""

from __future__ import annotations

from src.api.client import session
from src.utils.display import console, print_error


def route() -> None:
    """Route the authenticated user to the appropriate menu based on their role."""
    if not session.is_authenticated or session.role is None:
        print_error("Not authenticated. Please log in first.")
        return

    role = session.role.upper()

    if role == "ADMIN":
        _show_admin_menu()
    elif role == "MANAGER":
        _show_manager_menu()
    elif role == "EMPLOYEE":
        _show_employee_menu()
    else:
        print_error(f"Unknown role: {role}")


def _show_admin_menu() -> None:
    from src.screens.admin.menu import admin_menu
    admin_menu()


def _show_manager_menu() -> None:
    from src.screens.manager.menu import manager_menu
    manager_menu()


def _show_employee_menu() -> None:
    console.rule("[bold cyan]Employee Menu[/bold cyan]")
    console.print(
        "[dim]Employee features will be available in a future sprint. Press Enter to exit.[/dim]"
    )
    input()
