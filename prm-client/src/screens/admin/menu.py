"""Admin main menu."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from src.screens.admin.users_screen import users_screen
from src.screens.admin.employees_screen import employees_screen

console = Console()


def admin_menu() -> None:
    """Admin top-level menu loop."""
    while True:
        console.print(Panel("[bold cyan]Admin Menu[/bold cyan]"))
        console.print("  [1] Manage Users")
        console.print("  [2] Manage Employees & Skills")
        console.print("  [0] Logout")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            users_screen()
        elif choice == "2":
            employees_screen()
        elif choice == "0":
            console.print("[yellow]Logged out.[/yellow]")
            break
        else:
            console.print("[red]Invalid choice.[/red]")
