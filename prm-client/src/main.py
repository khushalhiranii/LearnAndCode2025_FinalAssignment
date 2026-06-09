"""PRM Client entry point."""

from __future__ import annotations

import sys

from src.screens import login_screen, menu_router
from src.utils.display import console


def main() -> None:
    try:
        authenticated = login_screen.show()
        if not authenticated:
            console.print("[dim]Exiting.[/dim]")
            sys.exit(0)
        menu_router.route()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye.[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
