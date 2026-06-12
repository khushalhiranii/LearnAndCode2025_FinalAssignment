"""
Shared HTTP client and session state.

SessionState is a module-level singleton kept in memory — never written to disk.
Call client.set_tokens() after a successful login/password-change.
"""

from __future__ import annotations

import httpx

from src.config import settings


class SessionState:
    """Holds in-memory auth state for the current console session."""

    def __init__(self) -> None:
        self.access_token: str | None = None
        self.role: str | None = None
        self.full_name: str | None = None

    def set_tokens(self, access_token: str, role: str, full_name: str) -> None:
        self.access_token = access_token
        self.role = role
        self.full_name = full_name

    def clear(self) -> None:
        self.access_token = None
        self.role = None
        self.full_name = None

    @property
    def is_authenticated(self) -> bool:
        return self.access_token is not None

    @property
    def auth_header(self) -> dict[str, str]:
        if not self.access_token:
            raise RuntimeError("No access token — user is not authenticated.")
        return {"Authorization": f"Bearer {self.access_token}"}


# Module-level singletons
session = SessionState()


def _raise_on_error(response: httpx.Response) -> None:
    if response.is_error:
        try:
            response.read()
            data = response.json()
            if "error" in data and "message" in data["error"]:
                raise RuntimeError(data["error"]["message"])
            if "detail" in data:
                if isinstance(data["detail"], list) and len(data["detail"]) > 0 and "msg" in data["detail"][0]:
                    raise RuntimeError(data["detail"][0]["msg"])
                raise RuntimeError(str(data["detail"]))
        except RuntimeError:
            raise
        except Exception:
            pass
        response.raise_for_status()


def get_client() -> httpx.Client:
    """Return a synchronous HTTP client pointed at the configured server."""
    return httpx.Client(
        base_url=settings.prm_server_base_url,
        timeout=10.0,
        event_hooks={'response': [_raise_on_error]}
    )
