"""Manager resource dashboard screen."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import manager_api

console = Console()


def _show_dashboard(data: dict) -> None:
    console.print(
        Panel(
            f"[bold]Team size:[/bold] {data['total_team_size']}   "
            f"[green]Allocated:[/green] {data['allocated_count']}   "
            f"[yellow]Bench:[/yellow] {data['bench_count']}",
            title="Resource Dashboard",
        )
    )

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Name")
    table.add_column("Status", width=12)
    table.add_column("Utilization %", justify="right", width=14)
    table.add_column("Active Allocations")

    for row in data["team"]:
        label_color = "green" if row["availability_label"] == "ALLOCATED" else "yellow"
        alloc_summary = ", ".join(
            f"P{a['project_id']}={a['utilization_percent']}%"
            for a in row.get("active_allocations", [])
        ) or "-"
        table.add_row(
            str(row["employee_id"]),
            row["employee_name"],
            f"[{label_color}]{row['availability_label']}[/{label_color}]",
            str(row["total_utilization_percent"]),
            alloc_summary,
        )

    console.print(table)


def dashboard_screen() -> None:
    """Display the resource dashboard for the current manager."""
    try:
        data = manager_api.get_dashboard()
        _show_dashboard(data)
    except Exception as exc:
        console.print(f"[red]Error loading dashboard: {exc}[/red]")
    console.input("\nPress Enter to continue...")
