"""Admin projects & milestones console screen."""

from __future__ import annotations

from rich.console import Console

from src.api import admin_api

console = Console()

_PROJECT_STATUSES = ["PLANNED", "ACTIVE", "ON_HOLD", "COMPLETED", "CANCELLED"]
_MILESTONE_STATUSES = ["NOT_STARTED", "IN_PROGRESS", "DONE", "CANCELLED"]


def projects_screen() -> None:
    """Admin projects menu loop."""
    while True:
        console.print("\n" + "=" * 60)
        console.print("                     MANAGE PROJECTS")
        console.print("=" * 60)
        console.print("  [1] Create Project")
        console.print("  [2] View All Projects")
        console.print("  [3] Update Project Details")
        console.print("  [4] Manage Milestones")
        console.print("  [0] Back to Admin Menu")
        console.print("-" * 60)

        choice = console.input("Select: ").strip()

        if choice == "1":
            _create_project()
        elif choice == "2":
            _list_projects()
        elif choice == "3":
            _update_project()
        elif choice == "4":
            _manage_milestones()
        elif choice == "0":
            break
        else:
            console.print("[red]Invalid choice.[/red]")


def _create_project() -> None:
    console.print("\n" + "=" * 60)
    console.print("                     CREATE PROJECT")
    console.print("=" * 60)
    
    name = console.input("Name: ").strip()
    description = console.input("Description (blank to skip): ").strip() or None
    manager_id_str = console.input("Manager User ID: ").strip()
    if manager_id_str.upper().startswith("U"):
        manager_id_str = manager_id_str[1:]
        
    total_sp_str = console.input("Total Story Points [0]: ").strip() or "0"
    
    # Defaults
    status = "PLANNED"

    payload: dict = {
        "name": name,
        "manager_user_id": int(manager_id_str),
        "status": status,
        "total_story_points": int(total_sp_str),
    }
    if description:
        payload["description"] = description

    try:
        project = admin_api.create_project(payload)
        console.print(f"\n[green]Project P{project['id']} Created Successfully![/green]")
    except Exception as exc:
        console.print(f"\n[red]Error: {exc}[/red]")


def _list_projects() -> None:
    status_filter = None
    while True:
        try:
            data = admin_api.list_projects(status=status_filter)
            items = data.get("items", [])
            
            console.print("\n" + "=" * 60)
            console.print("                     ALL PROJECTS")
            console.print("=" * 60)
            console.print(f"{'ID':<4}| {'Name':<18}| {'Status':<9}| {'Manager':<8}| Pts")
            console.print("-" * 60)
            
            if not items:
                console.print("No projects found.")
            else:
                for p in items:
                    pid = f"P{p['id']}"
                    name = p['name'][:18]
                    status = p['status'][:9]
                    manager = f"U{p['manager_user_id']}"
                    pts = f"{p['completed_story_points']}/{p['total_story_points']}"
                    console.print(f"{pid:<4}| {name:<18}| {status:<9}| {manager:<8}| {pts}")
                    
            console.print("-" * 60)
            console.print("Options:")
            console.print("  [F] Filter by Status  [B] Back to Manage Projects")
            
            action = console.input("\nSelect: ").strip().upper()
            if action == "B":
                break
            elif action == "F":
                status_input = console.input(f"Enter Status {_PROJECT_STATUSES} or blank to clear: ").strip()
                if status_input:
                    status_filter = status_input.upper()
                else:
                    status_filter = None
            else:
                console.print("[red]Invalid option.[/red]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            break


def _update_project() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  UPDATE PROJECT DETAILS")
    console.print("=" * 60)
    
    project_id_str = console.input("Project ID to update (e.g. P1): ").strip()
    if project_id_str.upper().startswith("P"):
        project_id_str = project_id_str[1:]
    project_id = int(project_id_str)

    console.print("Enter new values (leave blank to keep existing):")
    name = console.input("  New name: ").strip() or None
    status = console.input(f"  New status {_PROJECT_STATUSES}: ").strip() or None
    manager_id_str = console.input("  New manager user ID: ").strip()
    if manager_id_str.upper().startswith("U"):
        manager_id_str = manager_id_str[1:]
    total_sp_str = console.input("  Total story points: ").strip()

    payload: dict = {}
    if name:
        payload["name"] = name
    if status:
        payload["status"] = status.upper()
    if manager_id_str:
        payload["manager_user_id"] = int(manager_id_str)
    if total_sp_str:
        payload["total_story_points"] = int(total_sp_str)

    try:
        project = admin_api.update_project(project_id, payload)
        console.print(f"[green]Project P{project['id']} updated successfully.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _manage_milestones() -> None:
    project_id_str = console.input("\nEnter Project ID (e.g. P1): ").strip()
    if project_id_str.upper().startswith("P"):
        project_id_str = project_id_str[1:]
    project_id = int(project_id_str)

    while True:
        console.print("\n" + "=" * 60)
        console.print(f"                  MANAGE MILESTONES (P{project_id})")
        console.print("=" * 60)
        console.print("Current Milestones:")
        console.print(f"{'ID':<4}| {'Title':<16}| {'Status':<12}| {'Due Date':<10}| Pts")
        console.print("-" * 60)
        
        try:
            milestones = admin_api.list_milestones(project_id)
            if not milestones:
                console.print("No milestones found.")
            else:
                for m in milestones:
                    mid = f"M{m['id']}"
                    title = m['title'][:16]
                    status = m['status'][:12]
                    due = m.get('due_date') or "-"
                    pts = m['story_points']
                    console.print(f"{mid:<4}| {title:<16}| {status:<12}| {due:<10}| {pts}")
        except Exception as exc:
            console.print(f"[red]Error fetching milestones: {exc}[/red]")
            
        console.print("-" * 60)
        console.print("Options:")
        console.print("  [1] Add Milestone")
        console.print("  [2] Update Milestone Status")
        console.print("  [0] Back")
        
        choice = console.input("\nSelect: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            title = console.input("  Title: ").strip()
            due_date = console.input("  Due date YYYY-MM-DD (blank to skip): ").strip() or None
            sp_str = console.input("  Story points [0]: ").strip() or "0"
            payload: dict = {"title": title, "story_points": int(sp_str)}
            if due_date:
                payload["due_date"] = due_date
            try:
                m = admin_api.add_milestone(project_id, payload)
                console.print(f"[green]Milestone M{m['id']} added successfully.[/green]")
            except Exception as exc:
                console.print(f"[red]Error: {exc}[/red]")
        elif choice == "2":
            milestone_id_str = console.input("  Milestone ID (e.g. M1): ").strip()
            if milestone_id_str.upper().startswith("M"):
                milestone_id_str = milestone_id_str[1:]
            milestone_id = int(milestone_id_str)
            new_status = console.input(f"  New status {_MILESTONE_STATUSES}: ").strip().upper()
            try:
                m = admin_api.update_milestone_status(project_id, milestone_id, new_status)
                console.print(f"[green]Milestone M{m['id']} status updated to {m['status']}[/green]")
            except Exception as exc:
                console.print(f"[red]Error: {exc}[/red]")
        else:
            console.print("[red]Invalid choice.[/red]")
