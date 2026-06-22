from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI

from src.api.middleware.error_handler import register_exception_handlers
from src.api.routers.ai_router import router as ai_router
from src.api.routers.auth_router import router as auth_router
from src.api.routers.health_router import router as health_router
from src.api.routers.user_router import router as user_router
from src.api.routers.employee_router import router as employee_router
from src.api.routers.project_router import router as project_router
from src.api.routers.allocation_router import router as allocation_router
from src.api.routers.system_config_router import router as system_config_router
from src.api.routers.timesheet_router import router as timesheet_router
from src.api.routers.manager_project_router import router as manager_project_router
from src.api.routers.employee_self_router import router as employee_self_router
from src.config import settings
from src.infrastructure.database.engine import engine, AsyncSessionFactory
from src.infrastructure.scheduler.scheduler_runner import get_scheduler
from src.infrastructure.scheduler.daily_notification_scheduler import get_daily_scheduler
from src.infrastructure.unit_of_work import UnitOfWork

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("server_starting", environment=settings.environment)
    interval = 240
    try:
        async with AsyncSessionFactory() as session:
            uow = UnitOfWork(session)
            config = await uow.system_config.get_config()
            interval = config.scheduler_interval_minutes
    except Exception as exc:
        log.warning("scheduler_config_load_failed", error=str(exc))
    get_scheduler().start(interval_minutes=interval)
    get_daily_scheduler().start()
    yield
    get_daily_scheduler().stop()
    get_scheduler().stop()
    log.info("server_stopping")
    await engine.dispose()


app = FastAPI(
    title="PRM Tool API",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(user_router)
app.include_router(employee_router)
app.include_router(project_router)
app.include_router(manager_project_router)
app.include_router(allocation_router)
app.include_router(system_config_router)
app.include_router(timesheet_router)
app.include_router(employee_self_router)
app.include_router(ai_router)
