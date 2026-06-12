from datetime import date

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import require_manager
from src.application.dtos.timesheet_dtos import (
    ManagerTimesheetListResponse,
    TimesheetResponse,
)
from src.application.manager.timesheet_view_use_case import TimesheetViewUseCase
from src.domain.entities.user import User
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(tags=["timesheets"])


def _timesheet_view_use_case(uow: UnitOfWork) -> TimesheetViewUseCase:
    return TimesheetViewUseCase(
        uow.timesheets,
        uow.employees,
        uow.projects,
        uow.allocations,
    )


@router.get("/manager/timesheets", response_model=ManagerTimesheetListResponse)
async def list_manager_timesheets(
    week_start: date | None = Query(default=None),
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ManagerTimesheetListResponse:
    return await _timesheet_view_use_case(uow).list_team_timesheets(
        current_user.id, week_start
    )


@router.get(
    "/manager/timesheets/detail",
    response_model=TimesheetResponse,
    summary="View submitted timesheet detail for a team member",
)
async def get_manager_timesheet_detail(
    resource_profile_id: int = Query(...),
    week_start: date = Query(...),
    current_user: User = Depends(require_manager),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> TimesheetResponse:
    return await _timesheet_view_use_case(uow).get_team_timesheet_detail(
        current_user.id, resource_profile_id, week_start
    )
