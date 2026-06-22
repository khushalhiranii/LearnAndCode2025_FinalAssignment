from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AllocationAlreadyEndedError,
    AllocationNotFoundError,
    AllocationOverlapError,
    AuthorizationError,
    CannotDeactivateSelfError,
    DomainException,
    DuplicateEmailError,
    DuplicateProjectNameError,
    DuplicateSkillError,
    DuplicateUsernameError,
    EmployeeAlreadyExistsError,
    EmployeeNotFoundError,
    InactiveUserError,
    InvalidAllocationDateError,
    InvalidCredentialsError,
    InvalidManagerError,
    InvalidProjectManagerError,
    MilestoneNotFoundError,
    DuplicateTimesheetError,
    FutureWeekError,
    HoursCapExceededError,
    InvalidActivityTagError,
    ProjectNotActiveError,
    ProjectNotAllocatedError,
    ProjectNotFoundError,
    SkillNotFoundError,
    EmailDeliveryError,
    TimesheetSubmissionFrozenError,
    TeamQueryParseError,
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

    @app.exception_handler(EmployeeNotFoundError)
    async def handle_employee_not_found(
        request: Request, exc: EmployeeNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "EMPLOYEE_NOT_FOUND", "message": str(exc)},
            },
        )

    @app.exception_handler(SkillNotFoundError)
    async def handle_skill_not_found(
        request: Request, exc: SkillNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "SKILL_NOT_FOUND", "message": str(exc)},
            },
        )

    @app.exception_handler(TeamQueryParseError)
    async def handle_team_query_parse(
        request: Request, exc: TeamQueryParseError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "TEAM_QUERY_PARSE_ERROR", "message": str(exc)},
            },
        )

    @app.exception_handler(TimesheetSubmissionFrozenError)
    async def handle_timesheet_frozen(
        request: Request, exc: TimesheetSubmissionFrozenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {"code": "TIMESHEET_SUBMISSION_FROZEN", "message": str(exc)},
            },
        )

    @app.exception_handler(EmailDeliveryError)
    async def handle_email_delivery(
        request: Request, exc: EmailDeliveryError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": {"code": "EMAIL_DELIVERY_ERROR", "message": str(exc)},
            },
        )

    @app.exception_handler(DuplicateUsernameError)
    async def handle_duplicate_username(
        request: Request, exc: DuplicateUsernameError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "DUPLICATE_USERNAME", "message": str(exc)},
            },
        )

    @app.exception_handler(DuplicateEmailError)
    async def handle_duplicate_email(
        request: Request, exc: DuplicateEmailError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "DUPLICATE_EMAIL", "message": str(exc)},
            },
        )

    @app.exception_handler(DuplicateSkillError)
    async def handle_duplicate_skill(
        request: Request, exc: DuplicateSkillError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "DUPLICATE_SKILL", "message": str(exc)},
            },
        )

    @app.exception_handler(EmployeeAlreadyExistsError)
    async def handle_employee_already_exists(
        request: Request, exc: EmployeeAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "EMPLOYEE_ALREADY_EXISTS", "message": str(exc)},
            },
        )

    @app.exception_handler(InvalidManagerError)
    async def handle_invalid_manager(
        request: Request, exc: InvalidManagerError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "INVALID_MANAGER", "message": str(exc)},
            },
        )

    @app.exception_handler(CannotDeactivateSelfError)
    async def handle_cannot_deactivate_self(
        request: Request, exc: CannotDeactivateSelfError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "CANNOT_DEACTIVATE_SELF", "message": str(exc)},
            },
        )

    @app.exception_handler(ProjectNotFoundError)
    async def handle_project_not_found(
        request: Request, exc: ProjectNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "PROJECT_NOT_FOUND", "message": str(exc)},
            },
        )

    @app.exception_handler(MilestoneNotFoundError)
    async def handle_milestone_not_found(
        request: Request, exc: MilestoneNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "MILESTONE_NOT_FOUND", "message": str(exc)},
            },
        )

    @app.exception_handler(DuplicateProjectNameError)
    async def handle_duplicate_project_name(
        request: Request, exc: DuplicateProjectNameError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "DUPLICATE_PROJECT_NAME", "message": str(exc)},
            },
        )

    @app.exception_handler(InvalidProjectManagerError)
    async def handle_invalid_project_manager(
        request: Request, exc: InvalidProjectManagerError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "INVALID_PROJECT_MANAGER", "message": str(exc)},
            },
        )

    @app.exception_handler(AllocationNotFoundError)
    async def handle_allocation_not_found(
        request: Request, exc: AllocationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "ALLOCATION_NOT_FOUND", "message": str(exc)},
            },
        )

    @app.exception_handler(AllocationOverlapError)
    async def handle_allocation_overlap(
        request: Request, exc: AllocationOverlapError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "ALLOCATION_OVERLAP", "message": str(exc)},
            },
        )

    @app.exception_handler(AllocationAlreadyEndedError)
    async def handle_allocation_already_ended(
        request: Request, exc: AllocationAlreadyEndedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "ALLOCATION_ALREADY_ENDED", "message": str(exc)},
            },
        )

    @app.exception_handler(InvalidAllocationDateError)
    async def handle_invalid_allocation_date(
        request: Request, exc: InvalidAllocationDateError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "INVALID_ALLOCATION_DATE", "message": str(exc)},
            },
        )

    @app.exception_handler(ProjectNotActiveError)
    async def handle_project_not_active(
        request: Request, exc: ProjectNotActiveError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "PROJECT_NOT_ACTIVE", "message": str(exc)},
            },
        )

    @app.exception_handler(DuplicateTimesheetError)
    async def handle_duplicate_timesheet(
        request: Request, exc: DuplicateTimesheetError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {"code": "DUPLICATE_TIMESHEET", "message": str(exc)},
            },
        )

    @app.exception_handler(FutureWeekError)
    async def handle_future_week(
        request: Request, exc: FutureWeekError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "FUTURE_WEEK", "message": str(exc)},
            },
        )

    @app.exception_handler(ProjectNotAllocatedError)
    async def handle_project_not_allocated(
        request: Request, exc: ProjectNotAllocatedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "PROJECT_NOT_ALLOCATED", "message": str(exc)},
            },
        )

    @app.exception_handler(HoursCapExceededError)
    async def handle_hours_cap_exceeded(
        request: Request, exc: HoursCapExceededError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "HOURS_CAP_EXCEEDED", "message": str(exc)},
            },
        )

    @app.exception_handler(InvalidActivityTagError)
    async def handle_invalid_activity_tag(
        request: Request, exc: InvalidActivityTagError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "INVALID_ACTIVITY_TAG", "message": str(exc)},
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
