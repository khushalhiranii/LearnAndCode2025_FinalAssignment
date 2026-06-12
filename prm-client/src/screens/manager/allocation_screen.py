"""Manager allocation management screen."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import manager_api
from src.api import ai_api

console = Console()


# ─── helpers ──────────────────────────────────────────────────────────────────


def _show_allocations_table(allocations: list) -> None:
    if not allocations:
        console.print("[dim]No allocations found.[/dim]")
        return
    table = Table(title=f"Allocations ({len(allocations)} total)", show_header=True)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Employee ID", width=12)
    table.add_column("Project ID", width=10)
    table.add_column("Utilization %", justify="right", width=14)
    table.add_column("From", width=12)
    table.add_column("To", width=12)
    table.add_column("Status", width=10)
    for a in allocations:
        status_color = "green" if a["status"] == "ACTIVE" else "dim"
        table.add_row(
            str(a["id"]),
            str(a["resource_profile_id"]),
            str(a["project_id"]),
            str(a["utilization_percent"]),
            str(a["from_date"]),
            str(a["to_date"]),
            f"[{status_color}]{a['status']}[/{status_color}]",
        )
    console.print(table)


def _show_projects_table(projects: list) -> None:
    if not projects:
        console.print("[dim]No projects found.[/dim]")
        return
    table = Table(title="My Projects", show_header=True)
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Name")
    table.add_column("Status", width=12)
    for p in projects:
        table.add_row(str(p["id"]), p["name"], p["status"])
    console.print(table)


# ─── sub-screens ──────────────────────────────────────────────────────────────


def _list_allocations() -> None:
    try:
        # Note: Listing allocations for a manager isn't a direct endpoint right now.
        # It's better viewed via Dashboard. For now, print a helper.
        console.print("[dim]Please use the Resource Dashboard to view team allocations.[/dim]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _list_projects() -> None:
    try:
        response = manager_api.list_projects()
        if response:
            _show_projects_table(response["items"])
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _ai_allocate() -> None:
    query = console.input("\nDescribe requirement: ").strip()
    if len(query) < 3:
        console.print("[red]Query too short.[/red]")
        return
    try:
        console.print("[yellow]Searching...[/yellow]")
        result = ai_api.skill_match(query)
        matches = result.get("matches", [])
        if not matches:
            console.print("[dim]No matches.[/dim]")
            return
        for m in matches:
            console.print(f"  #{m['rank']} ID={m['resource_profile_id']} {m['full_name']} — {m['reason']}")
        sel = console.input("\nSelect # (0=cancel): ").strip()
        if not sel.isdigit() or int(sel) == 0:
            return
        match = next((m for m in matches if m["rank"] == int(sel)), None)
        if not match:
            console.print("[red]Invalid selection.[/red]")
            return
        project_id = int(console.input("Project ID: ").strip())
        utilization = int(console.input("Utilization %: ").strip())
        from_date = console.input("From date (YYYY-MM-DD): ").strip()
        to_date = console.input("To date (YYYY-MM-DD): ").strip()
        result = manager_api.allocate_employee(
            employee_id=match["resource_profile_id"],
            project_id=project_id,
            utilization_percent=utilization,
            from_date=from_date,
            to_date=to_date,
        )
        console.print(f"[green]Allocated {match['full_name']} — allocation ID {result['id']}[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _allocate_employee() -> None:
    console.print(Panel("[bold]Allocate Employee to Project[/bold]"))
    try:
        employee_id = int(console.input("Employee ID: ").strip())
        project_id = int(console.input("Project ID: ").strip())
        utilization = int(console.input("Utilization % (1-100): ").strip())
        from_date = console.input("From date (YYYY-MM-DD): ").strip()
        to_date = console.input("To date (YYYY-MM-DD): ").strip()

        result = manager_api.allocate_employee(
            employee_id=employee_id,
            project_id=project_id,
            utilization_percent=utilization,
            from_date=from_date,
            to_date=to_date,
        )
        console.print(
            f"[green]Allocation created — ID: {result['id']} "
            f"({result['utilization_percent']}% on project {result['project_id']})[/green]"
        )
    except ValueError as exc:
        console.print(f"[red]Invalid input: {exc}[/red]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _end_allocation() -> None:
    console.print(Panel("[bold]End Allocation[/bold]"))
    try:
        allocation_id = int(console.input("Allocation ID to end: ").strip())
        ended_at = console.input("End date (YYYY-MM-DD): ").strip()
        result = manager_api.end_allocation(allocation_id, ended_at)
        console.print(f"[green]Allocation {result['id']} ended successfully.[/green]")
    except ValueError as exc:
        console.print(f"[red]Invalid input: {exc}[/red]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


# ─── main screen ──────────────────────────────────────────────────────────────


def allocation_screen() -> None:
    """Allocation management sub-menu loop."""
    while True:
        console.print(Panel("[bold cyan]Allocation Management[/bold cyan]"))
        console.print("  [1] Find resource using AI (recommended)")
        console.print("  [2] Allocate employee directly")
        console.print("  [3] End an allocation")
        console.print("  [4] View my projects")
        console.print("  [0] Back")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            _ai_allocate()
        elif choice == "2":
            _allocate_employee()
        elif choice == "3":
            _end_allocation()
        elif choice == "4":
            _list_projects()
        elif choice == "0":
            break
        else:
            console.print("[red]Invalid choice.[/red]")
