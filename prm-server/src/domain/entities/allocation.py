from dataclasses import dataclass
from datetime import date, datetime

from src.domain.enums import AllocationStatus


@dataclass
class Allocation:
    id: int | None
    employee_id: int           # FK → employees.id
    project_id: int            # FK → projects.id
    utilization_percent: int   # 1–100; sum across active allocations must not exceed 100
    from_date: date
    to_date: date
    status: AllocationStatus   # ACTIVE | ENDED
    created_at: datetime
    updated_at: datetime
