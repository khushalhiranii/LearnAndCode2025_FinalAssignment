"""Manager timesheets screen."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import manager_api

console = Console()


def _show_timesheet_detail(detail: dict) -> None:
    console.print(Panel(f"[bold]Timesheet #{detail['id']} — Week {detail['week_start_date']}[/bold]"))
    console.print(f"  Total hours: {detail['total_hours']}")
    console.print(f"  Status:      {detail['status']}")
    if detail.get("entries"):
        table = Table(show_header=True)
        table.add_column("Project ID")
        table.add_column("Hours", justify="right")
        table.add_column("Activity Tags")
        for entry in detail["entries"]:
            tags = ", ".join(
                t.get("tag_name", str(t.get("activity_tag_id", "")))
                for t in entry.get("tags", [])
            ) or "-"
            table.add_row(str(entry["project_id"]), str(entry["hours_worked"]), tags)
        console.print(table)
    else:
        console.print("[dim]No entries.[/dim]")


def timesheets_screen() -> None:
    console.print(Panel("[bold cyan]Team Timesheets[/bold cyan]"))

    week_start = console.input(
        "Week Start Date (YYYY-MM-DD) or press Enter for current week: "
    ).strip()
    try:
        data = manager_api.list_timesheets(week_start if week_start else None)
        timesheets = data["items"]
        week = data["week_start_date"]

        table = Table(title=f"Timesheets for Week of {week}", show_header=True)
        table.add_column("Emp ID", style="cyan", width=7)
        table.add_column("Employee")
        table.add_column("Project")
        table.add_column("Hours", justify="right")
        table.add_column("Status")

        for ts in timesheets:
            status_color = "green" if ts["status"] == "SUBMITTED" else "red"
            table.add_row(
                str(ts.get("resource_profile_id", "")),
                ts["employee_name"],
                ts["project_name"],
                str(ts["hours"]),
                f"[{status_color}]{ts['status']}[/{status_color}]",
            )

        console.print(table)

        if timesheets:
            console.print("\nOptions:")
            console.print("  [D] View submitted timesheet detail")
            action = console.input("Select (Enter to continue): ").strip().upper()
            if action == "D":
                eid = console.input("Employee ID: ").strip()
                week_input = console.input(
                    f"Week start [{week}] (Enter to use listed week): "
                ).strip() or week
                if eid.isdigit():
                    detail = manager_api.get_timesheet_detail(int(eid), week_input)
                    console.print()
                    _show_timesheet_detail(detail)
    except Exception as exc:
        console.print(f"[red]Error loading timesheets: {exc}[/red]")
    console.input("\nPress Enter to continue...")
