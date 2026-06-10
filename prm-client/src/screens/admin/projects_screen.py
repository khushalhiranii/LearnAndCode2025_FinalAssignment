"""Admin projects & milestones console screen."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.api import admin_api

console = Console()

_PROJECT_STATUSES = ["PLANNED", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED"]
_MILESTONE_STATUSES = ["NOT_STARTED", "IN_PROGRESS", "DONE", "CANCELLED"]


# ─── helpers ──────────────────────────────────────────────────────────────────


def _show_projects_table(data: dict) -> None:
    table = Table(title=f"Projects (total: {data['total']})")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Manager ID")
    table.add_column("Points (done/total)")
    for p in data["items"]:
        table.add_row(
            str(p["id"]),
            p["name"],
            p["status"],
            str(p["manager_user_id"]),
            f"{p['completed_story_points']}/{p['total_story_points']}",
        )
    console.print(table)


def _show_milestones_table(milestones: list) -> None:
    table = Table(title="Milestones")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Due Date")
    table.add_column("Story Points")
    for m in milestones:
        table.add_row(
            str(m["id"]),
            m["title"],
            m["status"],
            str(m.get("due_date") or "-"),
            str(m["story_points"]),
        )
    console.print(table)


# ─── sub-screens ──────────────────────────────────────────────────────────────


def _list_projects() -> None:
    status_filter = console.input(
        "Filter by status (leave blank for all): "
    ).strip() or None
    try:
        data = admin_api.list_projects(status=status_filter)
        _show_projects_table(data)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _create_project() -> None:
    name = console.input("Project name: ").strip()
    description = console.input("Description (blank to skip): ").strip() or None
    manager_id_str = console.input("Manager user ID: ").strip()
    status = console.input(f"Status {_PROJECT_STATUSES} [PLANNED]: ").strip() or "PLANNED"
    total_sp_str = console.input("Total story points [0]: ").strip() or "0"
    start_date = console.input("Start date YYYY-MM-DD (blank to skip): ").strip() or None
    end_date = console.input("End date YYYY-MM-DD (blank to skip): ").strip() or None

    payload: dict = {
        "name": name,
        "manager_user_id": int(manager_id_str),
        "status": status,
        "total_story_points": int(total_sp_str),
    }
    if description:
        payload["description"] = description
    if start_date:
        payload["start_date"] = start_date
    if end_date:
        payload["end_date"] = end_date

    try:
        project = admin_api.create_project(payload)
        console.print(f"[green]Project created — ID: {project['id']}[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _update_project() -> None:
    project_id_str = console.input("Project ID to update: ").strip()
    project_id = int(project_id_str)

    console.print("Enter new values (leave blank to keep existing):")
    name = console.input("  New name: ").strip() or None
    status = console.input(f"  New status {_PROJECT_STATUSES}: ").strip() or None
    manager_id_str = console.input("  New manager user ID: ").strip()
    total_sp_str = console.input("  Total story points: ").strip()

    payload: dict = {}
    if name:
        payload["name"] = name
    if status:
        payload["status"] = status
    if manager_id_str:
        payload["manager_user_id"] = int(manager_id_str)
    if total_sp_str:
        payload["total_story_points"] = int(total_sp_str)

    try:
        project = admin_api.update_project(project_id, payload)
        console.print(f"[green]Project {project['id']} updated.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _manage_milestones() -> None:
    project_id_str = console.input("Project ID: ").strip()
    project_id = int(project_id_str)

    while True:
        console.print(Panel(f"[bold cyan]Milestones — Project {project_id}[/bold cyan]"))
        console.print("  [1] List milestones")
        console.print("  [2] Add milestone")
        console.print("  [3] Update milestone status")
        console.print("  [0] Back")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            try:
                milestones = admin_api.list_milestones(project_id)
                _show_milestones_table(milestones)
            except Exception as exc:
                console.print(f"[red]Error: {exc}[/red]")

        elif choice == "2":
            title = console.input("  Title: ").strip()
            due_date = console.input("  Due date YYYY-MM-DD (blank to skip): ").strip() or None
            sp_str = console.input("  Story points [0]: ").strip() or "0"
            payload: dict = {"title": title, "story_points": int(sp_str)}
            if due_date:
                payload["due_date"] = due_date
            try:
                m = admin_api.add_milestone(project_id, payload)
                console.print(f"[green]Milestone added — ID: {m['id']}[/green]")
            except Exception as exc:
                console.print(f"[red]Error: {exc}[/red]")

        elif choice == "3":
            milestone_id_str = console.input("  Milestone ID: ").strip()
            milestone_id = int(milestone_id_str)
            new_status = console.input(f"  New status {_MILESTONE_STATUSES}: ").strip()
            try:
                m = admin_api.update_milestone_status(project_id, milestone_id, new_status)
                console.print(f"[green]Milestone {m['id']} status → {m['status']}[/green]")
            except Exception as exc:
                console.print(f"[red]Error: {exc}[/red]")

        elif choice == "0":
            break


# ─── main entry ───────────────────────────────────────────────────────────────


def projects_screen() -> None:
    """Admin projects menu loop."""
    while True:
        console.print(Panel("[bold cyan]Manage Projects[/bold cyan]"))
        console.print("  [1] List projects")
        console.print("  [2] Create project")
        console.print("  [3] Update project")
        console.print("  [4] Manage milestones")
        console.print("  [0] Back")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "1":
            _list_projects()
        elif choice == "2":
            _create_project()
        elif choice == "3":
            _update_project()
        elif choice == "4":
            _manage_milestones()
        elif choice == "0":
            break
