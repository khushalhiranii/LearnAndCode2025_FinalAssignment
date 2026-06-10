"""Admin employee & skills management screen."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from src.api import admin_api

console = Console()


def employees_screen() -> None:
    """Admin sub-menu for employee and skill management."""
    while True:
        console.print("\n[bold cyan]Employee & Skills Management[/bold cyan]")
        console.print("  [1] List employees")
        console.print("  [2] Update employee details")
        console.print("  [3] Deactivate employee")
        console.print("  [4] Assign manager")
        console.print("  [5] Manage employee skills")
        console.print("  [6] List master skills")
        console.print("  [7] Create master skill")
        console.print("  [0] Back")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "0":
            break
        elif choice == "1":
            _list_employees()
        elif choice == "2":
            _update_employee()
        elif choice == "3":
            _deactivate_employee()
        elif choice == "4":
            _assign_manager()
        elif choice == "5":
            _manage_skills()
        elif choice == "6":
            _list_skills()
        elif choice == "7":
            _create_skill()
        else:
            console.print("[red]Invalid choice.[/red]")


def _list_employees() -> None:
    try:
        data = admin_api.list_employees()
        items = data["items"]
        if not items:
            console.print("[yellow]No employees found.[/yellow]")
            return
        table = Table(title=f"Employees (total: {data['total']})")
        table.add_column("ID", style="dim")
        table.add_column("Full Name")
        table.add_column("Email")
        table.add_column("Department")
        table.add_column("Designation")
        table.add_column("Manager ID")
        table.add_column("Active")
        for e in items:
            table.add_row(
                str(e["id"]),
                e["full_name"],
                e["email"],
                e.get("department") or "",
                e.get("designation") or "",
                str(e.get("manager_user_id") or ""),
                "✓" if e["is_active"] else "✗",
            )
        console.print(table)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _update_employee() -> None:
    eid = console.input("Employee ID: ").strip()
    department = console.input("Department (leave blank to skip): ").strip() or None
    designation = console.input("Designation (leave blank to skip): ").strip() or None
    doj = console.input("Date of joining YYYY-MM-DD (leave blank to skip): ").strip() or None
    try:
        data = admin_api.update_employee(int(eid), department, designation, doj)
        console.print(f"[green]Employee updated:[/green] {data}")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _deactivate_employee() -> None:
    eid = console.input("Employee ID to deactivate: ").strip()
    try:
        admin_api.deactivate_user(int(eid))  # cascades via DeactivateEmployeeUseCase
        console.print("[green]Employee deactivated.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _assign_manager() -> None:
    eid = console.input("Employee ID: ").strip()
    mid = console.input("Manager User ID: ").strip()
    try:
        data = admin_api.assign_manager(int(eid), int(mid))
        console.print(f"[green]Manager assigned.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _manage_skills() -> None:
    eid = console.input("Employee ID: ").strip()
    try:
        skills = admin_api.list_employee_skills(int(eid))
        if skills:
            table = Table(title="Employee Skills")
            table.add_column("Skill ID")
            table.add_column("Skill Name")
            table.add_column("Proficiency")
            for s in skills:
                table.add_row(str(s["skill_id"]), s["skill_name"], s["proficiency"])
            console.print(table)
        else:
            console.print("[yellow]No skills assigned.[/yellow]")

        console.print("\n  [a] Add skill  [r] Remove skill  [0] Back")
        action = console.input("Action: ").strip().lower()
        if action == "a":
            sid = console.input("Skill ID: ").strip()
            prof = console.input("Proficiency (BEGINNER/INTERMEDIATE/ADVANCED): ").strip().upper()
            admin_api.add_employee_skill(int(eid), int(sid), prof)
            console.print("[green]Skill added.[/green]")
        elif action == "r":
            sid = console.input("Skill ID to remove: ").strip()
            admin_api.remove_employee_skill(int(eid), int(sid))
            console.print("[green]Skill removed.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _list_skills() -> None:
    try:
        skills = admin_api.list_skills()
        if not skills:
            console.print("[yellow]No skills defined.[/yellow]")
            return
        table = Table(title="Master Skills")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Category")
        for s in skills:
            table.add_row(str(s["id"]), s["name"], s["category"])
        console.print(table)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _create_skill() -> None:
    name = console.input("Skill Name: ").strip()
    category = console.input("Category: ").strip()
    try:
        data = admin_api.create_skill(name, category)
        console.print(f"[green]Skill created: ID={data['id']}[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
