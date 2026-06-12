"""Admin view-all-allocations screen — BRD Screen 3.3."""

from __future__ import annotations

from rich.console import Console

from src.api import admin_api

console = Console()


def allocations_screen() -> None:
    """Admin view-all-allocations screen with optional filters (BRD Screen 3.3)."""
    while True:
        console.print("\n" + "=" * 60)
        console.print("                   VIEW ALL ALLOCATIONS")
        console.print("=" * 60)
        console.print("Filter options:")
        console.print("  [1] View all")
        console.print("  [2] Filter by Project ID")
        console.print("  [3] Filter by Employee ID")
        console.print("  [0] Back to Admin Menu")
        
        choice = console.input("\nSelect: ").strip()
        
        if choice == "0":
            break
            
        employee_id = None
        project_id = None
        
        if choice == "2":
            pid_str = console.input("Enter Project ID: ").strip()
            if pid_str.upper().startswith("P"):
                pid_str = pid_str[1:]
            if pid_str.isdigit():
                project_id = int(pid_str)
            else:
                console.print("[red]Invalid Project ID.[/red]")
                continue
        elif choice == "3":
            eid_str = console.input("Enter Employee ID: ").strip()
            if eid_str.upper().startswith("E"):
                eid_str = eid_str[1:]
            if eid_str.isdigit():
                employee_id = int(eid_str)
            else:
                console.print("[red]Invalid Employee ID.[/red]")
                continue
        elif choice != "1":
            console.print("[red]Invalid choice.[/red]")
            continue

        try:
            allocations = admin_api.list_all_allocations(
                employee_id=employee_id,
                project_id=project_id,
            )
            
            console.print("\n" + f"{'ID':<5}| {'Project':<8}| {'Employee':<9}| {'Allocation %':<13}| Status")
            console.print("-" * 60)
            if not allocations:
                console.print("No allocations found.")
            else:
                for a in allocations:
                    aid = f"A{a['id']}"
                    pid = f"P{a['project_id']}"
                    eid = f"E{a['resource_profile_id']}"
                    pct = f"{a['utilization_percent']}%"
                    status = a['status']
                    console.print(f"{aid:<5}| {pid:<8}| {eid:<9}| {pct:<13}| {status}")
            console.print("-" * 60)
        except Exception as exc:
            console.print(f"[red]Error fetching allocations: {exc}[/red]")
            
        console.input("Press [Enter] to return...")
