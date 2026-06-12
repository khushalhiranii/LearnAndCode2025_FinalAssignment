from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import employee_api

console = Console()


def _list_timesheets() -> None:
    console.clear()
    console.print(Panel("[bold cyan]My Timesheets[/bold cyan]"))

    try:
        timesheets = employee_api.list_timesheets()
        if not timesheets:
            console.print("[dim]No timesheets found.[/dim]")
        else:
            table = Table(title=f"Timesheet History ({len(timesheets)} total)", show_header=True)
            table.add_column("ID", style="cyan", width=5)
            table.add_column("Week Start", width=12)
            table.add_column("Hours", justify="right", width=8)
            table.add_column("Status", width=12)
            table.add_column("Submitted At")

            for ts in timesheets:
                status_color = "green" if ts["status"] == "SUBMITTED" else "dim"
                table.add_row(
                    str(ts["id"]),
                    str(ts["week_start_date"]),
                    str(ts["total_hours"]),
                    f"[{status_color}]{ts['status']}[/{status_color}]",
                    ts.get("submitted_at", "-") or "-",
                )

            console.print(table)
    except Exception as exc:
        console.print(f"[red]Error loading timesheets: {exc}[/red]")


def _submit_timesheet() -> None:
    console.clear()
    console.print(Panel("[bold cyan]Submit Timesheet[/bold cyan]"))

    try:
        week_start = console.input("Week Start Date (YYYY-MM-DD): ").strip()

        tags = employee_api.list_activity_tags()
        if tags:
            console.print("\n[bold]Available Activity Tags:[/bold]")
            for tag in tags:
                console.print(f"  [{tag['id']}] {tag['name']} ({tag['category']})")
        else:
            console.print("[yellow]No activity tags configured. Contact admin.[/yellow]")

        entries = []
        while True:
            console.print("\n[bold]Add an Entry[/bold]")
            project_str = console.input("Project ID (or press Enter to finish entries): ").strip()
            if not project_str:
                break

            project_id = int(project_str)
            hours = float(console.input("Hours Worked: ").strip())

            entry_tags = []
            while True:
                tag_str = console.input("Activity Tag ID (or press Enter to finish tags): ").strip()
                if not tag_str:
                    break
                tag_id = int(tag_str)
                selected = next((t for t in tags if t["id"] == tag_id), None)
                custom_text = None
                if selected and selected.get("category") == "OTHER":
                    custom_text = console.input("Custom tag description: ").strip() or None
                entry_tags.append({
                    "activity_tag_id": tag_id,
                    "custom_tag_text": custom_text,
                })

            entries.append({
                "project_id": project_id,
                "hours_worked": hours,
                "tags": entry_tags,
            })

        if not entries:
            console.print("[yellow]No entries added. Aborting.[/yellow]")
            return

        payload = {
            "week_start_date": week_start,
            "entries": entries
        }

        result = employee_api.submit_timesheet(payload)
        console.print(f"[green]Timesheet {result['id']} submitted successfully with {result['total_hours']} total hours![/green]")
    except ValueError as exc:
        console.print(f"[red]Invalid input: {exc}[/red]")
    except Exception as exc:
        console.print(f"[red]Error submitting timesheet: {exc}[/red]")


def timesheets_screen() -> None:
    """Timesheet sub-menu loop."""
    while True:
        console.clear()
        console.print(Panel("[bold cyan]Timesheets[/bold cyan]"))
        console.print("  [1] View timesheet history")
        console.print("  [2] Submit new timesheet")
        console.print("  [0] Back")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            _list_timesheets()
            console.input("\nPress Enter to continue...")
        elif choice == "2":
            _submit_timesheet()
            console.input("\nPress Enter to continue...")
        elif choice == "0":
            break
        else:
            console.print("[red]Invalid choice.[/red]")
            console.input("\nPress Enter to continue...")
