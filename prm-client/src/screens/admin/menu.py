"""Admin main menu."""

from __future__ import annotations

from rich.console import Console

from src.screens.admin.users_screen import users_screen
from src.screens.admin.employees_screen import employees_screen
from src.screens.admin.projects_screen import projects_screen
from src.screens.admin.system_config_screen import system_config_screen

console = Console()


def admin_menu() -> None:
    """Admin top-level menu loop."""
    while True:
        console.print("\n" + "=" * 60)
        console.print("                     ADMIN MENU")
        console.print("=" * 60)
        console.print("  [1] Manage Employees")
        console.print("  [2] Manage Projects")
        console.print("  [3] View All Allocations")
        console.print("  [4] Manage Users")
        console.print("  [5] System Configuration")
        console.print("  [0] Logout")
        console.print("-" * 60)

        choice = console.input("Select an option: ").strip()

        if choice == "1":
            employees_screen()
        elif choice == "2":
            projects_screen()
        elif choice == "3":
            from src.screens.admin.allocations_screen import allocations_screen
            allocations_screen()
        elif choice == "4":
            users_screen()
        elif choice == "5":
            system_config_screen()
        elif choice == "0":
            console.print("[yellow]Logging out...[/yellow]")
            break
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")
