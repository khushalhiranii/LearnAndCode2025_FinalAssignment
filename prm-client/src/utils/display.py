"""Console display helpers using Rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_header(title: str) -> None:
    console.print(Panel(Text(title, justify="center", style="bold cyan"), expand=False))


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")
