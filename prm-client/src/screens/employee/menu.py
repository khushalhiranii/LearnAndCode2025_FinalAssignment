from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from src.api.client import session
from src.screens.employee.allocations_screen import allocations_screen
from src.screens.employee.timesheets_screen import _list_timesheets, _submit_timesheet
from src.utils.display import console, print_error

console = Console()


def employee_menu() -> None:
    """Main menu loop for the EMPLOYEE role (BRD order: submit → history → allocations)."""
    while True:
        console.clear()
        console.print(Panel(f"[bold cyan]Employee Menu - Welcome, {session.full_name}[/bold cyan]"))
        try:
            from src.api import employee_api
            reminder = employee_api.get_missed_reminder()
            if reminder.get("has_missed"):
                console.print(
                    f"\n  [bold yellow]⚠ Reminder: Timesheet for week "
                    f"{reminder.get('week_start_date')} has not been submitted.[/bold yellow]"
                )
        except Exception:
            pass
        console.print("  [1] Submit Timesheet")
        console.print("  [2] View Timesheet History")
        console.print("  [3] My Allocations")
        console.print("  [0] Logout")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            _submit_timesheet()
            console.input("\nPress Enter to continue...")
        elif choice == "2":
            _list_timesheets()
            console.input("\nPress Enter to continue...")
        elif choice == "3":
            allocations_screen()
        elif choice == "0":
            session.clear()
            break
        else:
            print_error("Invalid choice. Please try again.")
            console.input("\nPress Enter to continue...")
