from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Employee:
    id: int | None
    user_id: int
    full_name: str           # denormalised from User for fast display
    email: str               # denormalised from User
    department: str | None
    designation: str | None
    date_of_joining: date | None
    manager_user_id: int | None   # FK → users.id where role=MANAGER
    is_active: bool
    created_at: datetime
    updated_at: datetime
