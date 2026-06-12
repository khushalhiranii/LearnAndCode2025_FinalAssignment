from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import employee_api

console = Console()


def allocations_screen() -> None:
    """Display the allocations for the current employee."""
    console.clear()
    console.print(Panel("[bold cyan]My Allocations[/bold cyan]"))

    try:
        allocations = employee_api.list_allocations()
        if not allocations:
            console.print("[dim]No allocations found.[/dim]")
        else:
            table = Table(title=f"Allocations ({len(allocations)} total)", show_header=True)
            table.add_column("ID", style="cyan", width=5)
            table.add_column("Project ID", width=12)
            table.add_column("Utilization %", justify="right", width=14)
            table.add_column("From", width=12)
            table.add_column("To", width=12)
            table.add_column("Status", width=10)

            for a in allocations:
                status_color = "green" if a["status"] == "ACTIVE" else "dim"
                table.add_row(
                    str(a["id"]),
                    str(a["project_id"]),
                    str(a["utilization_percent"]),
                    str(a["from_date"]),
                    str(a["to_date"]),
                    f"[{status_color}]{a['status']}[/{status_color}]",
                )

            console.print(table)

    except Exception as exc:
        console.print(f"[red]Error loading allocations: {exc}[/red]")

    console.input("\nPress Enter to continue...")
