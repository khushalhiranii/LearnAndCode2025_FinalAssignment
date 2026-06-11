# V6: Employee entity renamed to ResourceProfile.
# This file re-exports from resource_profile.py for backward compatibility.
# All new code should import from src.domain.entities.resource_profile directly.
from src.domain.entities.resource_profile import (  # noqa: F401
    ResourceProfile,
    ResourceSkill,
    Employee,
    EmployeeSkill,
)

