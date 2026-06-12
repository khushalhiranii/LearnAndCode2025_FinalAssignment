"""Manager AI Assistant screen."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from src.api import ai_api, manager_api

console = Console()

_HEALTH_COLORS = {
    "ON_TRACK": "green",
    "ATTENTION": "yellow",
    "AT_RISK": "red",
}


def ai_assistant_screen() -> None:
    while True:
        console.print(Panel("[bold cyan]AI Assistant[/bold cyan]"))
        console.print("  [1] Skill Match — find resources by natural language")
        console.print("  [2] Risk Summary — project health analysis")
        console.print("  [0] Back")
        choice = console.input("\nChoice: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            _skill_match_flow()
        elif choice == "2":
            _risk_summary_flow()
        else:
            console.print("[red]Invalid choice.[/red]")


def _skill_match_flow() -> None:
    query = console.input("\nDescribe your requirement: ").strip()
    if len(query) < 3:
        console.print("[red]Query too short.[/red]")
        return
    hours = console.input("Hours per week (optional, Enter to skip): ").strip()
    hours_val = float(hours) if hours else None
    try:
        console.print("\n[yellow]Searching... (AI matching in progress)[/yellow]")
        result = ai_api.skill_match(query, hours_per_week=hours_val)
        matches = result.get("matches", [])
        if not matches:
            console.print("[dim]No matches found.[/dim]")
        else:
            console.print("\n[bold]AI-MATCHED RESULTS[/bold]")
            for m in matches:
                console.print(
                    f"  #{m['rank']}  {m['full_name']}  "
                    f"(free {m['free_percent']}%) — {m['reason']}"
                )
            console.print(f"\n[dim]{result.get('note', '')}[/dim]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
    console.input("\nPress Enter to continue...")


def _risk_summary_flow() -> None:
    try:
        projects = manager_api.list_projects()
        items = projects.get("items", [])
        if not items:
            console.print("[dim]No projects found.[/dim]")
            return
        for i, p in enumerate(items, 1):
            color = _HEALTH_COLORS.get(p.get("health_status", "ON_TRACK"), "white")
            console.print(f"  [{i}] {p['name']}  [{color}]{p.get('health_status', 'N/A')}[/{color}]")
        sel = console.input("\nSelect project number: ").strip()
        if not sel.isdigit() or int(sel) < 1 or int(sel) > len(items):
            return
        project = items[int(sel) - 1]
        console.print("\n[yellow]Generating AI summary...[/yellow]")
        result = ai_api.risk_summary(project["id"])
        console.print(Panel(result.get("summary", "No summary available.")))
        if not result.get("ai_generated"):
            console.print("[dim](Rule-based fallback — LLM unavailable)[/dim]")
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
    console.input("\nPress Enter to continue...")
