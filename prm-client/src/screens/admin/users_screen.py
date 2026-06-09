"""Admin user management screen."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from src.api import admin_api

console = Console()


def users_screen() -> None:
    """Admin sub-menu for user management."""
    while True:
        console.print("\n[bold cyan]User Management[/bold cyan]")
        console.print("  [1] List users")
        console.print("  [2] Create user")
        console.print("  [3] Deactivate user")
        console.print("  [4] Reactivate user")
        console.print("  [5] Reset user password")
        console.print("  [0] Back")

        choice = console.input("\n[bold]Choice:[/bold] ").strip()

        if choice == "0":
            break
        elif choice == "1":
            _list_users()
        elif choice == "2":
            _create_user()
        elif choice == "3":
            _deactivate_user()
        elif choice == "4":
            _reactivate_user()
        elif choice == "5":
            _reset_password()
        else:
            console.print("[red]Invalid choice.[/red]")


def _list_users() -> None:
    try:
        data = admin_api.list_users()
        items = data["items"]
        if not items:
            console.print("[yellow]No users found.[/yellow]")
            return
        table = Table(title=f"Users (total: {data['total']})")
        table.add_column("ID", style="dim")
        table.add_column("Username")
        table.add_column("Full Name")
        table.add_column("Role")
        table.add_column("Active")
        for u in items:
            table.add_row(
                str(u["id"]),
                u["username"],
                u["full_name"],
                u["role"],
                "✓" if u["is_active"] else "✗",
            )
        console.print(table)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _create_user() -> None:
    username = console.input("Username: ").strip()
    email = console.input("Email: ").strip()
    full_name = console.input("Full Name: ").strip()
    role = console.input("Role (ADMIN/MANAGER/EMPLOYEE): ").strip().upper()
    try:
        data = admin_api.create_user(username, email, full_name, role)
        console.print(f"[green]User created.[/green] Temp password: [bold]{data['temp_password']}[/bold]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _deactivate_user() -> None:
    uid = console.input("User ID to deactivate: ").strip()
    try:
        admin_api.deactivate_user(int(uid))
        console.print("[green]User deactivated.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _reactivate_user() -> None:
    uid = console.input("User ID to reactivate: ").strip()
    try:
        admin_api.reactivate_user(int(uid))
        console.print("[green]User reactivated.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _reset_password() -> None:
    uid = console.input("User ID for password reset: ").strip()
    try:
        data = admin_api.reset_password(int(uid))
        console.print(f"[green]Password reset.[/green] Temp password: [bold]{data['temp_password']}[/bold]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
