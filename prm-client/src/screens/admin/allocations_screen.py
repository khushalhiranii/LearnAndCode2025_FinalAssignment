"""Admin view-all-allocations screen — BRD Screen 3.3."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import admin_api

console = Console()


def _show_allocations_table(allocations: list) -> None:
    if not allocations:
        console.print("[yellow]No allocations found.[/yellow]")
        return
    table = Table(title=f"All Allocations ({len(allocations)} total)", show_header=True)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Employee ID", width=12)
    table.add_column("Project ID", width=10)
    table.add_column("%", justify="right", width=6)
    table.add_column("From", width=12)
    table.add_column("To", width=12)
    table.add_column("Status", width=10)
    for a in allocations:
        status_color = "green" if a["status"] == "ACTIVE" else "dim"
        table.add_row(
            str(a["id"]),
            str(a["employee_id"]),
            str(a["project_id"]),
            f"{a['utilization_percent']}%",
            str(a["from_date"]),
            str(a["to_date"]),
            f"[{status_color}]{a['status']}[/{status_color}]",
        )
    console.print(table)


def allocations_screen() -> None:
    """Admin view-all-allocations screen with optional filters (BRD Screen 3.3)."""
    console.print(Panel("[bold]ALL ALLOCATIONS[/bold]"))
    console.print("Press Enter to show all, or enter a filter value.")

    emp_raw = console.input("Filter by Employee ID (blank = all): ").strip()
    proj_raw = console.input("Filter by Project ID  (blank = all): ").strip()

    employee_id = int(emp_raw) if emp_raw else None
    project_id = int(proj_raw) if proj_raw else None

    try:
        allocations = admin_api.list_all_allocations(
            employee_id=employee_id,
            project_id=project_id,
        )
        _show_allocations_table(allocations)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")

    console.input("\nPress Enter to continue...")
