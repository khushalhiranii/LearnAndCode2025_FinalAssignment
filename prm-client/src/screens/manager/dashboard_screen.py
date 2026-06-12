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
    table.add_column("Dept", width=10)
    table.add_column("Status", width=12)
    table.add_column("Util %", justify="right", width=8)
    table.add_column("Skills")
    table.add_column("Allocations")

    for row in data["team"]:
        label_color = "green" if row["availability_label"] == "ALLOCATED" else "yellow"
        alloc_summary = ", ".join(
            f"P{a['project_id']}={a['utilization_percent']}%"
            for a in row.get("active_allocations", [])
        ) or "-"
        skills = ", ".join(row.get("skills", [])) or "-"
        table.add_row(
            str(row["resource_profile_id"]),
            row["full_name"],
            (row.get("department") or "-")[:10],
            f"[{label_color}]{row['availability_label']}[/{label_color}]",
            str(row["total_utilization_percent"]),
            skills[:40] + ("..." if len(skills) > 40 else ""),
            alloc_summary,
        )

    console.print(table)


def _show_employee_detail(row: dict) -> None:
    console.print(Panel(f"[bold]Employee E{row['resource_profile_id']} — {row['full_name']}[/bold]"))
    console.print(f"  Department:   {row.get('department') or '-'}")
    console.print(f"  Designation:  {row.get('designation') or '-'}")
    console.print(f"  Status:       {row['availability_label']} ({row['total_utilization_percent']}%)")
    skills = row.get("skills") or []
    if skills:
        console.print("  Skills:")
        for skill in skills:
            console.print(f"    • {skill}")
    else:
        console.print("  Skills:       (none)")

    allocs = row.get("active_allocations") or []
    if allocs:
        console.print("  Active allocations:")
        for a in allocs:
            console.print(
                f"    A{a['id']}: Project P{a['project_id']} — "
                f"{a['utilization_percent']}% ({a['from_date']} → {a['to_date']})"
            )
    else:
        console.print("  Active allocations: (none)")


def dashboard_screen() -> None:
    """Display the resource dashboard for the current manager."""
    try:
        data = manager_api.get_dashboard()
        _show_dashboard(data)

        detail_id = console.input(
            "\nEnter Employee ID for details (or press Enter to skip): "
        ).strip()
        if detail_id:
            if detail_id.upper().startswith("E"):
                detail_id = detail_id[1:]
            if detail_id.isdigit():
                match = next(
                    (r for r in data["team"] if r["resource_profile_id"] == int(detail_id)),
                    None,
                )
                if match:
                    console.print()
                    _show_employee_detail(match)
                else:
                    console.print("[yellow]Employee not found on your team.[/yellow]")
            else:
                console.print("[red]Invalid ID.[/red]")
    except Exception as exc:
        console.print(f"[red]Error loading dashboard: {exc}[/red]")
    console.input("\nPress Enter to continue...")
