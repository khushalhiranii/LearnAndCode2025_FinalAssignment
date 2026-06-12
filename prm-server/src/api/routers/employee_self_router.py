from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user
from src.application.dtos.allocation_dtos import AllocationResponse
from src.application.dtos.timesheet_dtos import (
    ActivityTagResponse,
    SubmitTimesheetRequest,
    TimesheetResponse,
)
from src.application.employee.allocation_use_case import EmployeeAllocationUseCase
from src.application.employee.timesheet_use_case import EmployeeTimesheetUseCase
from src.domain.entities.user import User
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/employee", tags=["employee"])


def _timesheet_use_case(uow: UnitOfWork) -> EmployeeTimesheetUseCase:
    return EmployeeTimesheetUseCase(
        uow.timesheets,
        uow.employees,
        uow.activity_tags,
        uow.allocations,
        uow.system_config,
    )


@router.get("/activity-tags", response_model=list[ActivityTagResponse])
async def list_activity_tags(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[ActivityTagResponse]:
    return await _timesheet_use_case(uow).list_activity_tags()


@router.get("/allocations", response_model=list[AllocationResponse])
async def list_my_allocations(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[AllocationResponse]:
    use_case = EmployeeAllocationUseCase(uow.allocations, uow.employees)
    return await use_case.list_my_allocations(current_user.id)


@router.get("/timesheets", response_model=list[TimesheetResponse])
async def list_my_timesheets(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[TimesheetResponse]:
    return await _timesheet_use_case(uow).list_my_timesheets(current_user.id)


@router.post("/timesheets", response_model=TimesheetResponse, status_code=status.HTTP_201_CREATED)
async def submit_timesheet(
    request: SubmitTimesheetRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TimesheetResponse:
    return await _timesheet_use_case(uow).submit_timesheet(current_user.id, request)


@router.get("/timesheets/missed-reminder")
async def missed_timesheet_reminder(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    """Return whether the employee has a missed timesheet for the prior week."""
    from datetime import date, timedelta
    from src.domain.enums import TimesheetStatus

    employee = await uow.employees.find_by_user_id(current_user.id)
    if employee is None or employee.id is None:
        return {"has_missed": False, "week_start_date": None}

    today = date.today()
    prior_monday = today - timedelta(days=today.weekday() + 7)
    ts = await uow.timesheets.find_by_employee_and_week(employee.id, prior_monday)
    has_missed = ts is not None and ts.status == TimesheetStatus.MISSED
    has_allocation = bool(
        await uow.allocations.find_active_by_employee_and_week(employee.id, prior_monday)
    )
    return {
        "has_missed": has_missed or (has_allocation and ts is None),
        "week_start_date": prior_monday.isoformat(),
    }
