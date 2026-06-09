from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AuthorizationError,
    DomainException,
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
    WeakPasswordError,
)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(InvalidCredentialsError)
    async def handle_invalid_credentials(
        request: Request, exc: InvalidCredentialsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {"code": "INVALID_CREDENTIALS", "message": str(exc)},
            },
        )

    @app.exception_handler(InactiveUserError)
    async def handle_inactive_user(
        request: Request, exc: InactiveUserError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {"code": "INACTIVE_USER", "message": str(exc)},
            },
        )

    @app.exception_handler(AuthorizationError)
    async def handle_authorization_error(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {"code": "FORBIDDEN", "message": str(exc)},
            },
        )

    @app.exception_handler(UserNotFoundError)
    async def handle_user_not_found(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": str(exc)},
            },
        )

    @app.exception_handler(WeakPasswordError)
    async def handle_weak_password(
        request: Request, exc: WeakPasswordError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "WEAK_PASSWORD", "message": str(exc)},
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces to clients
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                },
            },
        )
