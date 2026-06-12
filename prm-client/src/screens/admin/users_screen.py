"""Admin users management console screen."""

from __future__ import annotations

from rich.console import Console

from src.api import admin_api

console = Console()

_ROLES = ["ADMIN", "MANAGER", "EMPLOYEE"]


def users_screen() -> None:
    """Admin users menu loop."""
    while True:
        console.print("\n" + "=" * 60)
        console.print("                     MANAGE USERS")
        console.print("=" * 60)
        console.print("  [1] Create User Account")
        console.print("  [2] View All Users")
        console.print("  [3] Reset User Password")
        console.print("  [4] Deactivate User")
        console.print("  [5] Reactivate User")
        console.print("  [0] Back to Admin Menu")
        console.print("-" * 60)

        choice = console.input("Select: ").strip()

        if choice == "1":
            _create_user()
        elif choice == "2":
            _list_users()
        elif choice == "3":
            _reset_password()
        elif choice == "4":
            _deactivate_user()
        elif choice == "5":
            _reactivate_user()
        elif choice == "0":
            break
        else:
            console.print("[red]Invalid choice.[/red]")


def _create_user() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  CREATE USER ACCOUNT")
    console.print("=" * 60)
    
    username = console.input("Username: ").strip()
    email = console.input("Email: ").strip()
    full_name = console.input("Full Name: ").strip()
    role = console.input("Role [ADMIN | MANAGER | EMPLOYEE]: ").strip().upper()

    try:
        data = admin_api.create_user(username, email, full_name, role)
        console.print(f"\n[green]User U{data['id']} created successfully![/green]")
        console.print(f"Temporary Password: [bold]{data['temp_password']}[/bold]")
        console.print("[yellow]⚠ Please share this password securely with the user.[/yellow]")
    except Exception as exc:
        console.print(f"\n[red]Error: {exc}[/red]")


def _list_users() -> None:
    role_filter = None
    while True:
        try:
            data = admin_api.list_users(role=role_filter)
            items = data.get("items", [])
            
            console.print("\n" + "=" * 60)
            console.print("                     ALL USERS")
            console.print("=" * 60)
            console.print(f"{'ID':<4}| {'Username':<15}| {'Role':<12}| Status")
            console.print("-" * 60)
            
            if not items:
                console.print("No users found.")
            else:
                for u in items:
                    uid = f"U{u['id']}"
                    uname = u['username'][:15]
                    role = u['role'][:12]
                    status = "Active" if u['is_account_enabled'] else "Inact"
                    console.print(f"{uid:<4}| {uname:<15}| {role:<12}| {status}")
                    
            console.print("-" * 60)
            console.print("Options:")
            console.print("  [F] Filter by Role    [B] Back to Manage Users")
            
            action = console.input("\nSelect: ").strip().upper()
            if action == "B":
                break
            elif action == "F":
                role_input = console.input(f"Enter Role {_ROLES} or blank to clear: ").strip()
                if role_input:
                    role_filter = role_input.upper()
                else:
                    role_filter = None
            else:
                console.print("[red]Invalid option.[/red]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            break


def _reset_password() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  RESET USER PASSWORD")
    console.print("=" * 60)
    
    uid_str = console.input("Enter User ID: ").strip()
    if uid_str.upper().startswith("U"):
        uid_str = uid_str[1:]
        
    try:
        user_id = int(uid_str)
        data = admin_api.reset_password(user_id)
        console.print(f"[green]Password for User U{user_id} reset successfully![/green]")
        console.print(f"New Temporary Password: [bold]{data['temp_password']}[/bold]")
        console.print("[yellow]⚠ User will be forced to change this upon next login.[/yellow]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _deactivate_user() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  DEACTIVATE USER")
    console.print("=" * 60)
    
    uid_str = console.input("Enter User ID to deactivate: ").strip()
    if uid_str.upper().startswith("U"):
        uid_str = uid_str[1:]
        
    confirm = console.input(f"Are you sure you want to deactivate U{uid_str}? (Y/N): ").strip().upper()
    if confirm == "Y":
        try:
            admin_api.deactivate_user(int(uid_str))
            console.print(f"[green]User U{uid_str} deactivated successfully.[/green]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
    else:
        console.print("Operation cancelled.")


def _reactivate_user() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  REACTIVATE USER")
    console.print("=" * 60)

    uid_str = console.input("Enter User ID to reactivate: ").strip()
    if uid_str.upper().startswith("U"):
        uid_str = uid_str[1:]

    confirm = console.input(f"Reactivate U{uid_str}? (Y/N): ").strip().upper()
    if confirm == "Y":
        try:
            admin_api.reactivate_user(int(uid_str))
            console.print(f"[green]User U{uid_str} reactivated successfully.[/green]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
    else:
        console.print("Operation cancelled.")
