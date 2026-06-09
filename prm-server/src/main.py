from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI

from src.api.middleware.error_handler import register_exception_handlers
from src.api.routers.auth_router import router as auth_router
from src.api.routers.health_router import router as health_router
from src.api.routers.user_router import router as user_router
from src.api.routers.employee_router import router as employee_router
from src.config import settings
from src.infrastructure.database.engine import engine

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("server_starting", environment=settings.environment)
    yield
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
