from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums import Role


@dataclass
class User:
    id: int | None
    full_name: str
    email: str
    username: str
    password_hash: str
    role: Role
    is_active: bool
    force_password_change: bool
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
