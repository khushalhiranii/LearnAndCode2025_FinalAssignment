from datetime import datetime, timezone

from src.application.dtos.employee_dtos import (
    AddSkillRequest,
    EmployeeSkillResponse,
    SkillResponse,
    UpdateSkillRequest,
    CreateSkillRequest,
)
from src.domain.exceptions import (
    DuplicateSkillError,
    EmployeeNotFoundError,
    SkillNotFoundError,
)
from src.domain.entities.skill import Skill
from src.domain.ports.repositories import IEmployeeRepository, ISkillRepository


class SkillUseCase:
    """Handles all master-skill CRUD and employee-skill assignment operations."""

    def __init__(
        self,
        skill_repo: ISkillRepository,
        employee_repo: IEmployeeRepository,
    ) -> None:
        self._skills = skill_repo
        self._employees = employee_repo

    # ── master skills ─────────────────────────────────────────────────────────

    async def create_skill(self, request: CreateSkillRequest) -> SkillResponse:
        existing = await self._skills.find_by_name(request.name)
        if existing is not None:
            raise DuplicateSkillError(f"Skill '{request.name}' already exists.")

        now = datetime.now(timezone.utc)
        skill = Skill(
            id=None,
            name=request.name,
            category=request.category,
            created_at=now,
            updated_at=now,
        )
        saved = await self._skills.save(skill)
        return _skill_to_response(saved)

    async def list_skills(self) -> list[SkillResponse]:
        skills = await self._skills.find_all()
        return [_skill_to_response(s) for s in skills]

    # ── employee skills ───────────────────────────────────────────────────────

    async def add_skill_to_employee(
        self, employee_id: int, request: AddSkillRequest
    ) -> EmployeeSkillResponse:
        if await self._employees.find_by_id(employee_id) is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        if await self._skills.find_by_id(request.skill_id) is None:
            raise SkillNotFoundError(f"Skill {request.skill_id} not found.")

        existing = await self._employees.find_employee_skill(employee_id, request.skill_id)
        if existing is not None:
            raise DuplicateSkillError(
                f"Employee {employee_id} already has skill {request.skill_id}."
            )

        emp_skill = await self._employees.add_skill(
            employee_id, request.skill_id, request.proficiency
        )
        return _emp_skill_to_response(emp_skill)

    async def update_employee_skill(
        self, employee_id: int, skill_id: int, request: UpdateSkillRequest
    ) -> EmployeeSkillResponse:
        emp_skill = await self._employees.find_employee_skill(employee_id, skill_id)
        if emp_skill is None:
            raise SkillNotFoundError(
                f"Employee {employee_id} does not have skill {skill_id}."
            )
        await self._employees.update_skill_proficiency(emp_skill.id, request.proficiency)  # type: ignore[arg-type]
        emp_skill.proficiency = request.proficiency
        return _emp_skill_to_response(emp_skill)

    async def remove_employee_skill(self, employee_id: int, skill_id: int) -> None:
        emp_skill = await self._employees.find_employee_skill(employee_id, skill_id)
        if emp_skill is None:
            raise SkillNotFoundError(
                f"Employee {employee_id} does not have skill {skill_id}."
            )
        await self._employees.remove_skill(emp_skill.id)  # type: ignore[arg-type]

    async def list_employee_skills(self, employee_id: int) -> list[EmployeeSkillResponse]:
        if await self._employees.find_by_id(employee_id) is None:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found.")
        skills = await self._employees.find_skills(employee_id)
        return [_emp_skill_to_response(s) for s in skills]


def _skill_to_response(skill: Skill) -> SkillResponse:
    return SkillResponse(
        id=skill.id,  # type: ignore[arg-type]
        name=skill.name,
        category=skill.category,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


def _emp_skill_to_response(es) -> EmployeeSkillResponse:  # type: ignore[no-untyped-def]
    from src.domain.entities.skill import EmployeeSkill
    return EmployeeSkillResponse(
        id=es.id,
        employee_id=es.employee_id,
        skill_id=es.skill_id,
        skill_name=es.skill_name,
        proficiency=es.proficiency,
        created_at=es.created_at,
        updated_at=es.updated_at,
    )
