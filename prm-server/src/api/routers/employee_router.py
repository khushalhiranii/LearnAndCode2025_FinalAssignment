from fastapi import APIRouter, Depends, Query

from src.api.dependencies import require_admin
from src.application.admin.assign_manager_use_case import AssignManagerUseCase
from src.application.admin.deactivate_employee_use_case import DeactivateEmployeeUseCase
from src.application.admin.list_employees_use_case import ListEmployeesUseCase
from src.application.admin.skill_use_case import SkillUseCase
from src.application.admin.update_employee_use_case import UpdateEmployeeUseCase
from src.application.dtos.employee_dtos import (
    AddSkillRequest,
    AssignManagerRequest,
    CreateSkillRequest,
    UpdateEmployeeRequest,
    UpdateSkillRequest,
)
from src.domain.entities.user import User
from src.infrastructure.unit_of_work import UnitOfWork, get_unit_of_work

router = APIRouter(prefix="/admin", tags=["admin-employees"])


# ── employees ─────────────────────────────────────────────────────────────────

@router.get("/employees", response_model=dict)
async def list_employees(
    is_active: bool | None = Query(None),
    manager_user_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = ListEmployeesUseCase(uow.users, uow.employees)
    result = await use_case.execute(
        is_active=is_active, manager_user_id=manager_user_id, page=page, page_size=page_size
    )
    return {"success": True, "data": result.model_dump()}


@router.patch("/employees/{employee_id}", response_model=dict)
async def update_employee(
    employee_id: int,
    request: UpdateEmployeeRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = UpdateEmployeeUseCase(uow.users, uow.employees)
    result = await use_case.execute(employee_id, request)
    return {"success": True, "data": result.model_dump()}


@router.post("/employees/{employee_id}/deactivate", response_model=dict)
async def deactivate_employee(
    employee_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = DeactivateEmployeeUseCase(uow.users, uow.employees)
    result = await use_case.execute(employee_id, acting_admin_id=current_user.id)  # type: ignore[arg-type]
    return {"success": True, "data": result.model_dump()}


@router.post("/employees/{employee_id}/assign-manager", response_model=dict)
async def assign_manager(
    employee_id: int,
    request: AssignManagerRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = AssignManagerUseCase(uow.users, uow.employees)
    result = await use_case.execute(employee_id, request.manager_user_id)
    return {"success": True, "data": result.model_dump()}


# ── employee skills ───────────────────────────────────────────────────────────

@router.get("/employees/{employee_id}/skills", response_model=dict)
async def list_employee_skills(
    employee_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SkillUseCase(uow.skills, uow.employees)
    result = await use_case.list_employee_skills(employee_id)
    return {"success": True, "data": [r.model_dump() for r in result]}


@router.post("/employees/{employee_id}/skills", response_model=dict, status_code=201)
async def add_skill_to_employee(
    employee_id: int,
    request: AddSkillRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SkillUseCase(uow.skills, uow.employees)
    result = await use_case.add_skill_to_employee(employee_id, request)
    return {"success": True, "data": result.model_dump()}


@router.patch("/employees/{employee_id}/skills/{skill_id}", response_model=dict)
async def update_employee_skill(
    employee_id: int,
    skill_id: int,
    request: UpdateSkillRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SkillUseCase(uow.skills, uow.employees)
    result = await use_case.update_employee_skill(employee_id, skill_id, request)
    return {"success": True, "data": result.model_dump()}


@router.delete("/employees/{employee_id}/skills/{skill_id}", status_code=204)
async def remove_employee_skill(
    employee_id: int,
    skill_id: int,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    use_case = SkillUseCase(uow.skills, uow.employees)
    await use_case.remove_employee_skill(employee_id, skill_id)


# ── master skills ─────────────────────────────────────────────────────────────

@router.get("/skills", response_model=dict)
async def list_skills(
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SkillUseCase(uow.skills, uow.employees)
    result = await use_case.list_skills()
    return {"success": True, "data": [r.model_dump() for r in result]}


@router.post("/skills", response_model=dict, status_code=201)
async def create_skill(
    request: CreateSkillRequest,
    current_user: User = Depends(require_admin),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    use_case = SkillUseCase(uow.skills, uow.employees)
    result = await use_case.create_skill(request)
    return {"success": True, "data": result.model_dump()}
