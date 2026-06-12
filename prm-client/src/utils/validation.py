"""Input validation helpers for console prompts."""

from __future__ import annotations

import re


def validate_not_empty(value: str, field_name: str = "Field") -> str:
    """Raise ValueError if value is blank."""
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


def validate_password_strength(password: str) -> list[str]:
    """Return a list of violation messages. Empty list means the password is valid."""
    errors: list[str] = []
    if len(password) < 8:
        errors.append("At least 8 characters required.")
    if not re.search(r"[A-Z]", password):
        errors.append("Must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Must contain at least one special character.")
    return errors
