"""PRM Client entry point."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.screens import login_screen, menu_router
from src.utils.display import console


def main() -> None:
    try:
        while True:
            authenticated = login_screen.show()
            if not authenticated:
                console.print("[dim]Exiting.[/dim]")
                break
            
            # This blocks until the user logs out or exits from the menu
            menu_router.route()
            
            # Clear the screen after logout so the new login prompt is clean
            console.clear()
            console.print("[green]Successfully logged out.[/green]\n")
            
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye.[/dim]")
        sys.exit(0)

if __name__ == "__main__":
    main()
