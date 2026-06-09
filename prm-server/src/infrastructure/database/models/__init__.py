# Import all ORM models here so Alembic env.py picks them up via Base.metadata.
from src.infrastructure.database.engine import Base  # noqa: F401
from src.infrastructure.database.models.user_model import UserModel  # noqa: F401
