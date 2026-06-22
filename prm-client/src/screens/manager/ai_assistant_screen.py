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
        console.print("  [3] Team Builder — describe whole team in one sentence")
        console.print("  [0] Back")
        choice = console.input("\nChoice: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            _skill_match_flow()
        elif choice == "2":
            _risk_summary_flow()
        elif choice == "3":
            _team_builder_flow()
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


_PROFICIENCY_MAP = {
    "b": "BEGINNER",
    "beginner": "BEGINNER",
    "i": "INTERMEDIATE",
    "intermediate": "INTERMEDIATE",
    "a": "ADVANCED",
    "advanced": "ADVANCED",
}


def _team_builder_flow() -> None:
    mode = console.input(
        "\n[M] Describe team in natural language  [S] Structured (manual roles)  [Enter]=M: "
    ).strip().upper()
    if mode == "S":
        _team_builder_structured_flow()
    else:
        _team_builder_natural_language_flow()


def _team_builder_natural_language_flow() -> None:
    try:
        query = console.input(
            "\nDescribe your team need (e.g. 'a new banking portal needing a "
            "Senior Java Developer, a DevOps Engineer and a QA tester'): "
        ).strip()
        if len(query) < 10:
            console.print("[red]Please provide a more detailed description.[/red]")
            return

        console.print("\n[yellow]Parsing roles and matching team in one pass...[/yellow]")
        result = ai_api.team_builder_from_query(query)
        _display_team_builder_result(result)

        if not result.get("ai_parsed"):
            console.print(
                "[dim](Roles parsed with rule-based fallback — LLM unavailable or "
                "response could not be parsed)[/dim]"
            )
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
    console.input("\nPress Enter to continue...")


def _team_builder_structured_flow() -> None:
    try:
        skills = ai_api.list_skills()
        if not skills:
            console.print("[dim]No skills in catalog. Ask admin to add skills first.[/dim]")
            return

        console.print("\n[bold]Available skills[/bold]")
        for s in skills:
            console.print(f"  [{s['id']}] {s['name']}  ({s.get('category', '')})")

        count_raw = console.input("\nHow many roles do you need? ").strip()
        if not count_raw.isdigit() or int(count_raw) < 1:
            console.print("[red]Enter a positive number.[/red]")
            return
        role_count = int(count_raw)

        roles: list[dict] = []
        for i in range(role_count):
            console.print(f"\n[bold]Role {i + 1}[/bold]")
            title = console.input("  Role title (e.g. Senior Java Developer): ").strip()
            skill_raw = console.input("  Skill ID from list above: ").strip()
            prof_raw = console.input(
                "  Min proficiency [B]eginner / [I]nmediate / [A]dvanced (default B): "
            ).strip().lower() or "b"
            util_raw = console.input("  Utilization % (default 100): ").strip() or "100"

            if not title or not skill_raw.isdigit():
                console.print("[red]Role title and valid skill ID are required.[/red]")
                return
            proficiency = _PROFICIENCY_MAP.get(prof_raw)
            if proficiency is None:
                console.print("[red]Invalid proficiency.[/red]")
                return
            if not util_raw.isdigit() or int(util_raw) < 1 or int(util_raw) > 100:
                console.print("[red]Utilization must be 1–100.[/red]")
                return

            roles.append(
                {
                    "role_title": title,
                    "skill_id": int(skill_raw),
                    "min_proficiency": proficiency,
                    "utilization_percent": int(util_raw),
                }
            )

        console.print("\n[yellow]Matching team in a single pass...[/yellow]")
        result = ai_api.team_builder(roles)
        _display_team_builder_result(result)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
    console.input("\nPress Enter to continue...")


def _display_team_builder_result(result: dict) -> None:
    parsed = result.get("parsed_roles")
    if parsed:
        console.print("\n[bold]PARSED ROLES[/bold]")
        for role in parsed:
            console.print(
                f"  • {role['role_title']} — {role['skill_name']} "
                f"({role['min_proficiency']})"
            )

    console.print("\n[bold]TEAM BUILDER RESULTS[/bold]")
    for role in result.get("roles", []):
        if role.get("filled"):
            console.print(
                f"  [green]✓[/green] {role['role_title']}: "
                f"{role['full_name']} ({role['proficiency']} {role['skill_name']}, "
                f"free {role['free_percent']}%)"
            )
            if role.get("reason"):
                console.print(f"      [dim]{role['reason']}[/dim]")
        else:
            console.print(f"  [red]✗[/red] {role['role_title']}: [red]Unfilled[/red]")
            if role.get("reason"):
                console.print(f"      [dim]{role['reason']}[/dim]")

    gaps = result.get("gaps", [])
    if gaps:
        console.print("\n[bold yellow]Gaps[/bold yellow]")
        for gap in gaps:
            label = gap.get("gap_type", "GAP")
            console.print(f"  [{label}] {gap['role_title']}: {gap['message']}")
            if gap.get("available_from"):
                console.print(f"      Available from: {gap['available_from']}")

    if result.get("all_roles_filled"):
        console.print("\n[green]All roles filled — no gaps.[/green]")
    console.print(f"\n[dim]{result.get('note', '')}[/dim]")
