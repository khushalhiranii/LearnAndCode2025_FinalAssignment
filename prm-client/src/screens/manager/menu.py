"""Manager main menu."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

console = Console()


def manager_menu() -> None:
    """Manager top-level menu loop."""
    while True:
        console.print(Panel("[bold cyan]Manager Menu[/bold cyan]"))
        console.print("  [1] Resource Dashboard")
        console.print("  [2] Manage Allocations")
        console.print("  [0] Logout")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            from src.screens.manager.dashboard_screen import dashboard_screen
            dashboard_screen()
        elif choice == "2":
            from src.screens.manager.allocation_screen import allocation_screen
            allocation_screen()
        elif choice == "0":
            console.print("[yellow]Logged out.[/yellow]")
            break
        else:
            console.print("[red]Invalid choice.[/red]")
