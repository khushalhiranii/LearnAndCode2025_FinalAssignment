"""Admin System Configuration screen."""

from __future__ import annotations

from rich.console import Console
from src.api import admin_api

console = Console()


def system_config_screen() -> None:
    """Admin system configuration loop."""
    while True:
        try:
            config = admin_api.get_system_config()
        except Exception as exc:
            console.print(f"[red]Error fetching config: {exc}[/red]")
            return

        provider = config.get("llm_provider", "Not Set")
        api_key = config.get("llm_api_key", "")
        base_url = config.get("llm_base_url", "Not Set")
        model = config.get("llm_model", "Not Set")
        display_key = "*" * len(api_key) if api_key else "Not Set"
        interval = config.get("scheduler_interval_hours", config.get("scheduler_interval_minutes", 240) // 60)
        max_hours = config.get("max_weekly_hours", 40)

        console.print("\n" + "=" * 60)
        console.print("                     SYSTEM CONFIGURATION")
        console.print("=" * 60)
        console.print("\nCurrent Settings:")
        console.print(f"  [1] LLM Provider:         {provider}")
        console.print(f"  [2] LLM API Key:          {display_key}")
        console.print(f"  [3] LLM Base URL:         {base_url}")
        console.print(f"  [4] LLM Model:            {model}")
        console.print(f"  [5] Scheduler Interval:   Every {interval} hours")
        console.print(f"  [6] Max Weekly Hours:     {max_hours} hours/week")
        console.print("\n" + "-" * 60)
        console.print("Options:")
        console.print("  [#] Enter number to update setting")
        console.print("  [0] Back to Admin Menu")

        choice = console.input("\nSelect: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            new_val = console.input("Enter new LLM Provider: ").strip()
            if new_val:
                try:
                    admin_api.update_system_config({"llm_provider": new_val})
                    console.print("[green]LLM Provider updated.[/green]")
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
        elif choice == "2":
            new_val = console.input("Enter new LLM API Key: ").strip()
            if new_val:
                try:
                    admin_api.update_system_config({"llm_api_key": new_val})
                    console.print("[green]LLM API Key updated.[/green]")
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
        elif choice == "3":
            new_val = console.input("Enter LLM Base URL: ").strip()
            if new_val:
                try:
                    admin_api.update_system_config({"llm_base_url": new_val})
                    console.print("[green]LLM Base URL updated.[/green]")
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
        elif choice == "4":
            new_val = console.input("Enter LLM Model: ").strip()
            if new_val:
                try:
                    admin_api.update_system_config({"llm_model": new_val})
                    console.print("[green]LLM Model updated.[/green]")
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
        elif choice == "5":
            new_val = console.input("Enter new Scheduler Interval (hours): ").strip()
            if new_val.isdigit():
                try:
                    admin_api.update_system_config({"scheduler_interval_hours": int(new_val)})
                    console.print("[green]Scheduler Interval updated.[/green]")
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
            else:
                console.print("[red]Invalid input. Must be an integer.[/red]")
        elif choice == "6":
            new_val = console.input("Enter new Max Weekly Hours: ").strip()
            if new_val.isdigit():
                try:
                    admin_api.update_system_config({"max_weekly_hours": int(new_val)})
                    console.print("[green]Max Weekly Hours updated.[/green]")
                except Exception as exc:
                    console.print(f"[red]Error: {exc}[/red]")
            else:
                console.print("[red]Invalid input. Must be an integer.[/red]")
        else:
            console.print("[red]Invalid choice.[/red]")
