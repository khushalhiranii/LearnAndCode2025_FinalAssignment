"""Manager projects screen with health detail."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import ai_api, manager_api

console = Console()

_HEALTH_LABELS = {
    "ON_TRACK": ("green", "ON TRACK"),
    "ATTENTION": ("yellow", "ATTENTION"),
    "AT_RISK": ("red", "AT RISK"),
}


def projects_screen() -> None:
    while True:
        console.print(Panel("[bold cyan]My Projects[/bold cyan]"))
        try:
            data = manager_api.list_projects()
            items = data.get("items", [])
            table = Table(show_header=True)
            table.add_column("#", width=3)
            table.add_column("Name")
            table.add_column("Status")
            table.add_column("Health")
            table.add_column("SP Done/Total", justify="right")

            for i, p in enumerate(items, 1):
                color, label = _HEALTH_LABELS.get(p.get("health_status", "ON_TRACK"), ("white", "N/A"))
                table.add_row(
                    str(i),
                    p["name"],
                    p["status"],
                    f"[{color}]{label}[/{color}]",
                    f"{p['completed_story_points']}/{p['total_story_points']}",
                )
            console.print(table)

            sel = console.input("\nSelect project # for details (0=Back): ").strip()
            if sel == "0":
                break
            if sel.isdigit() and 1 <= int(sel) <= len(items):
                _show_project_detail(items[int(sel) - 1]["id"])
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            console.input("\nPress Enter to continue...")
            break


def _show_project_detail(project_id: int) -> None:
    try:
        detail = manager_api.get_project_detail(project_id)
        color, label = _HEALTH_LABELS.get(detail.get("health_status", "ON_TRACK"), ("white", "N/A"))
        console.print(Panel(f"[bold]{detail['name']}[/bold] — [{color}]{label}[/{color}]"))

        if detail.get("risk_flags"):
            console.print("\n[bold]Risk Flags:[/bold]")
            for flag in detail["risk_flags"]:
                console.print(f"  [red]✗[/red]  {flag}")

        console.print("\n[bold]Milestones:[/bold]")
        for m in detail.get("milestones", []):
            console.print(f"  • {m['title']}  due {m.get('due_date', 'N/A')}  [{m['status']}]")

        console.print("\n[bold]Allocated Resources:[/bold]")
        for a in detail.get("allocations", []):
            console.print(
                f"  Resource {a['resource_profile_id']}  {a['utilization_percent']}%  "
                f"{a['from_date']} → {a['to_date']}"
            )

        action = console.input("\n[A] Get AI Risk Summary  [Enter] Back: ").strip().upper()
        if action == "A":
            console.print("\n[yellow]Generating AI summary...[/yellow]")
            result = ai_api.risk_summary(project_id)
            console.print(Panel(result.get("summary", "")))
            console.print(f"[dim]{result.get('note', 'AI-generated from milestone and timesheet data.')}[/dim]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
    console.input("\nPress Enter to continue...")
