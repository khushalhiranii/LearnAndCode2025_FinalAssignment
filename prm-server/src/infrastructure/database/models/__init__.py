# Import all ORM models here so Alembic env.py picks them up via Base.metadata.
from src.infrastructure.database.engine import Base  # noqa: F401
from src.infrastructure.database.models.user_model import UserModel  # noqa: F401
from src.infrastructure.database.models.skill_model import SkillModel  # noqa: F401
from src.infrastructure.database.models.employee_model import EmployeeModel, EmployeeSkillModel  # noqa: F401
from src.infrastructure.database.models.project_model import ProjectModel  # noqa: F401
from src.infrastructure.database.models.milestone_model import MilestoneModel  # noqa: F401
