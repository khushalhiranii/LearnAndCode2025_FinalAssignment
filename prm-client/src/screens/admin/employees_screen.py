"""Admin employee & skills management screen."""

from __future__ import annotations

from rich.console import Console

from src.api import admin_api

console = Console()


def employees_screen() -> None:
    """Admin sub-menu for employee and skill management."""
    while True:
        console.print("\n" + "=" * 60)
        console.print("                     MANAGE EMPLOYEES")
        console.print("=" * 60)
        console.print("  [1] View All Employees")
        console.print("  [2] Update Employee")
        console.print("  [3] Deactivate Employee")
        console.print("  [4] Manage Employee Skills")
        console.print("  [5] Assign Manager")
        console.print("  [0] Back to Admin Menu")
        console.print("-" * 60)

        choice = console.input("Select: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            _view_all_employees()
        elif choice == "2":
            _update_employee()
        elif choice == "3":
            _deactivate_employee()
        elif choice == "4":
            _manage_skills()
        elif choice == "5":
            _assign_manager()
        else:
            console.print("[red]Invalid choice.[/red]")


def _view_all_employees() -> None:
    status_filter = None
    while True:
        try:
            # We fetch employees, filtering by status if active
            # The API uses is_active=True/False. Let's map string filters to bools if needed.
            is_active_param = None
            if status_filter == "Active":
                is_active_param = True
            elif status_filter == "Inactive":
                is_active_param = False
            
            data = admin_api.list_employees(is_active=is_active_param)
            items = data["items"]
            
            console.print("\n" + "=" * 60)
            console.print("                     ALL EMPLOYEES")
            console.print("=" * 60)
            console.print(f"{'ID':<4}| {'Name':<14}| {'Dept':<8}| {'Work':<9}| {'Status':<7}| Alloc")
            console.print("-" * 60)
            
            if not items:
                console.print("No employees found.")
            else:
                for e in items:
                    emp_id = f"E{e['id']}"
                    name = (e['full_name'] or '')[:13]
                    dept = (e.get('department') or '')[:7]
                    work = e.get("work_status", "BENCH")[:8]
                    status = "Active" if e['is_available'] else "Inact"
                    
                    # Fetch active allocations to get count (mocked to 0 if not returned by list_employees)
                    allocs = 0
                    try:
                        # Find allocations for this employee
                        alloc_data = admin_api.list_all_allocations(employee_id=e['id'])
                        active_allocs = [a for a in alloc_data if a.get('status') == 'ACTIVE']
                        allocs = len(active_allocs)
                    except Exception:
                        pass
                    
                    console.print(f"{emp_id:<4}| {name:<14}| {dept:<8}| {work:<9}| {status:<7}| {allocs}")
                    
            console.print("-" * 60)
            console.print("Options:")
            console.print("  [F] Filter by Status  [B] Back to Manage Employees")
            
            action = console.input("\nSelect: ").strip().upper()
            if action == "B":
                break
            elif action == "F":
                # Prompt for status
                status_input = console.input("Enter Status (Active/Inactive) or leave blank to clear: ").strip()
                if status_input.lower() == "active":
                    status_filter = "Active"
                elif status_input.lower() == "inactive":
                    status_filter = "Inactive"
                else:
                    status_filter = None
            else:
                console.print("[red]Invalid option.[/red]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            break


def _update_employee() -> None:
    eid_str = console.input("\nEnter Employee ID: ").strip()
    if eid_str.upper().startswith("E"):
        eid_str = eid_str[1:]
    if not eid_str.isdigit():
        console.print("[red]Invalid ID.[/red]")
        return
    dept = console.input("Department (Enter to skip): ").strip() or None
    designation = console.input("Designation (Enter to skip): ").strip() or None
    doj = console.input("Date of joining YYYY-MM-DD (Enter to skip): ").strip() or None
    try:
        admin_api.update_employee(int(eid_str), department=dept, designation=designation, date_of_joining=doj)
        console.print("[green]Employee updated.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _deactivate_employee() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  DEACTIVATE EMPLOYEE")
    console.print("=" * 60)
    
    eid_str = console.input("Enter Employee ID to deactivate: ").strip()
    # Strip 'E' if user entered 'E1'
    if eid_str.upper().startswith("E"):
        eid_str = eid_str[1:]
        
    if not eid_str.isdigit():
        console.print("[red]Invalid ID format.[/red]")
        return
        
    eid = int(eid_str)
    
    # Check active allocations
    try:
        alloc_data = admin_api.list_all_allocations(employee_id=eid)
        active_allocs = [a for a in alloc_data if a.get('status') == 'ACTIVE']
        alloc_count = len(active_allocs)
        
        if alloc_count > 0:
            console.print(f"\n[bold yellow]⚠ Warning: This employee has {alloc_count} active allocations![/bold yellow]")
            console.print("[bold yellow]Deactivating will terminate their assignments immediately.[/bold yellow]\n")
            
        confirm = console.input("Proceed? (Y/N): ").strip().upper()
        if confirm == "Y":
            admin_api.deactivate_employee(eid)
            console.print("[green]Employee deactivated.[/green]")
        else:
            console.print("Operation cancelled.")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _assign_manager() -> None:
    console.print("\n" + "=" * 60)
    console.print("                  ASSIGN MANAGER")
    console.print("=" * 60)
    
    eid_str = console.input("Enter Employee ID: ").strip()
    mid_str = console.input("Enter Manager ID (User ID): ").strip()
    
    if eid_str.upper().startswith("E"):
        eid_str = eid_str[1:]
    if mid_str.upper().startswith("E") or mid_str.upper().startswith("U"):
        mid_str = mid_str[1:]
        
    try:
        admin_api.assign_manager(int(eid_str), int(mid_str))
        console.print("[green]Manager assigned successfully.[/green]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


def _manage_skills() -> None:
    console.print("\n" + "=" * 60)
    console.print("               MANAGE EMPLOYEE SKILLS")
    console.print("=" * 60)
    
    eid_str = console.input("Enter Employee ID: ").strip()
    if eid_str.upper().startswith("E"):
        eid_str = eid_str[1:]
        
    if not eid_str.isdigit():
        console.print("[red]Invalid Employee ID.[/red]")
        return
        
    eid = int(eid_str)
    
    while True:
        try:
            skills = admin_api.list_employee_skills(eid)
            console.print(f"\nSkills for Employee E{eid}:")
            if not skills:
                console.print("  (No skills assigned)")
            else:
                for s in skills:
                    console.print(f"  - [{s['skill_id']}] {s['skill_name']} ({s['proficiency']})")
                    
            console.print("\nOptions:")
            console.print("  [A] Add Skill  [U] Update Proficiency  [R] Remove Skill  [L] List Master Skills  [B] Back")
            
            action = console.input("Select: ").strip().upper()
            if action == "B":
                break
            elif action == "L":
                master_skills = admin_api.list_skills()
                console.print("\nMaster Skills:")
                for ms in master_skills:
                    console.print(f"  [{ms['id']}] {ms['name']} ({ms['category']})")
            elif action == "A":
                sid = console.input("Enter Skill ID: ").strip()
                prof = console.input("Enter Proficiency (BEGINNER/INTERMEDIATE/ADVANCED): ").strip().upper()
                if sid.isdigit() and prof in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]:
                    admin_api.add_employee_skill(eid, int(sid), prof)
                    console.print("[green]Skill added.[/green]")
                else:
                    console.print("[red]Invalid input.[/red]")
            elif action == "U":
                sid = console.input("Enter Skill ID to update: ").strip()
                prof = console.input("New Proficiency (BEGINNER/INTERMEDIATE/ADVANCED): ").strip().upper()
                if sid.isdigit() and prof in ["BEGINNER", "INTERMEDIATE", "ADVANCED"]:
                    admin_api.update_employee_skill(eid, int(sid), prof)
                    console.print("[green]Proficiency updated.[/green]")
                else:
                    console.print("[red]Invalid input.[/red]")
            elif action == "R":
                sid = console.input("Enter Skill ID to remove: ").strip()
                if sid.isdigit():
                    admin_api.remove_employee_skill(eid, int(sid))
                    console.print("[green]Skill removed.[/green]")
                else:
                    console.print("[red]Invalid input.[/red]")
            else:
                console.print("[red]Invalid choice.[/red]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            break
