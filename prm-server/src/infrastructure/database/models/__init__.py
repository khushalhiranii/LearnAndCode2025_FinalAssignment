# Import all ORM models here so Alembic env.py picks them up via Base.metadata.
from src.infrastructure.database.engine import Base  # noqa: F401
from src.infrastructure.database.models.user_model import UserModel  # noqa: F401
from src.infrastructure.database.models.role_model import RoleModel, UserRoleModel  # noqa: F401
from src.infrastructure.database.models.skill_model import SkillModel  # noqa: F401
from src.infrastructure.database.models.employee_model import (  # noqa: F401
    ResourceProfileModel,
    ResourceSkillModel,
)
from src.infrastructure.database.models.resource_hierarchy_model import ResourceHierarchyModel  # noqa: F401
from src.infrastructure.database.models.project_model import ProjectModel  # noqa: F401
from src.infrastructure.database.models.milestone_model import MilestoneModel  # noqa: F401
from src.infrastructure.database.models.allocation_model import AllocationModel  # noqa: F401
from src.infrastructure.database.models.system_config_model import SystemConfigModel  # noqa: F401
from src.infrastructure.database.models.timesheet_model import (  # noqa: F401
    ActivityTagModel,
    TimesheetModel,
    TimesheetEntryModel,
    TimesheetEntryActivityTagModel,
)
from src.infrastructure.database.models.project_health_model import (  # noqa: F401
    ProjectHealthSnapshotModel,
    AISuggestionAuditModel,
)
