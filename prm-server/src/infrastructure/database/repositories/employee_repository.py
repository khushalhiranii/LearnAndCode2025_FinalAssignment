from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.employee import Employee, EmployeeSkill
from src.domain.entities.skill import Skill
from src.domain.enums import ProficiencyLevel
from src.domain.ports.repositories import IEmployeeRepository
from src.infrastructure.database.models.employee_model import EmployeeModel, EmployeeSkillModel
from src.infrastructure.database.models.skill_model import SkillModel


class SQLAlchemyEmployeeRepository(IEmployeeRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── private mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: EmployeeModel) -> Employee:
        return Employee(
            id=model.id,
            user_id=model.user_id,
            full_name="",    # populated by caller from User data when needed
            email="",        # populated by caller from User data when needed
            department=model.department,
            designation=model.designation,
            date_of_joining=model.date_of_joining,
            manager_user_id=model.manager_user_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _skill_to_entity(model: EmployeeSkillModel, skill: SkillModel | None = None) -> EmployeeSkill:
        return EmployeeSkill(
            id=model.id,
            employee_id=model.employee_id,
            skill_id=model.skill_id,
            skill_name=skill.name if skill else "",
            proficiency=ProficiencyLevel(model.proficiency),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ── IEmployeeRepository ──────────────────────────────────────────────────

    async def find_by_id(self, employee_id: int) -> Employee | None:
        result = await self._session.execute(
            select(EmployeeModel).where(EmployeeModel.id == employee_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_user_id(self, user_id: int) -> Employee | None:
        result = await self._session.execute(
            select(EmployeeModel).where(EmployeeModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all(
        self,
        is_active: bool | None = None,
        manager_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        from sqlalchemy import func

        q = select(EmployeeModel)
        if is_active is not None:
            q = q.where(EmployeeModel.is_active == is_active)
        if manager_user_id is not None:
            q = q.where(EmployeeModel.manager_user_id == manager_user_id)

        count_result = await self._session.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count_result.scalar_one()

        q = q.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(q)).scalars().all()
        return [self._to_entity(m) for m in rows], total

    async def save(self, employee: Employee) -> Employee:
        model = EmployeeModel()
        if employee.id is not None:
            model.id = employee.id
        model.user_id = employee.user_id
        model.department = employee.department
        model.designation = employee.designation
        model.date_of_joining = employee.date_of_joining
        model.manager_user_id = employee.manager_user_id
        model.is_active = employee.is_active
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_active(self, employee_id: int, is_active: bool) -> None:
        await self._session.execute(
            update(EmployeeModel)
            .where(EmployeeModel.id == employee_id)
            .values(is_active=is_active, updated_at=datetime.now(timezone.utc))
        )

    async def update_manager(
        self, employee_id: int, manager_user_id: int | None
    ) -> None:
        await self._session.execute(
            update(EmployeeModel)
            .where(EmployeeModel.id == employee_id)
            .values(manager_user_id=manager_user_id, updated_at=datetime.now(timezone.utc))
        )

    # ── skills ────────────────────────────────────────────────────────────────

    async def find_skills(self, employee_id: int) -> list[EmployeeSkill]:
        result = await self._session.execute(
            select(EmployeeSkillModel, SkillModel)
            .join(SkillModel, EmployeeSkillModel.skill_id == SkillModel.id)
            .where(EmployeeSkillModel.employee_id == employee_id)
        )
        return [
            self._skill_to_entity(es_model, skill_model)
            for es_model, skill_model in result.all()
        ]

    async def find_employee_skill(
        self, employee_id: int, skill_id: int
    ) -> EmployeeSkill | None:
        result = await self._session.execute(
            select(EmployeeSkillModel, SkillModel)
            .join(SkillModel, EmployeeSkillModel.skill_id == SkillModel.id)
            .where(
                EmployeeSkillModel.employee_id == employee_id,
                EmployeeSkillModel.skill_id == skill_id,
            )
        )
        row = result.first()
        if row is None:
            return None
        es_model, skill_model = row
        return self._skill_to_entity(es_model, skill_model)

    async def add_skill(
        self,
        employee_id: int,
        skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> EmployeeSkill:
        model = EmployeeSkillModel()
        model.employee_id = employee_id
        model.skill_id = skill_id
        model.proficiency = proficiency.value
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        skill_result = await self._session.execute(
            select(SkillModel).where(SkillModel.id == skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        return self._skill_to_entity(model, skill)

    async def update_skill_proficiency(
        self,
        employee_skill_id: int,
        proficiency: ProficiencyLevel,
    ) -> None:
        await self._session.execute(
            update(EmployeeSkillModel)
            .where(EmployeeSkillModel.id == employee_skill_id)
            .values(proficiency=proficiency.value, updated_at=datetime.now(timezone.utc))
        )

    async def remove_skill(self, employee_skill_id: int) -> None:
        result = await self._session.execute(
            select(EmployeeSkillModel).where(EmployeeSkillModel.id == employee_skill_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)

    async def find_by_manager(self, manager_user_id: int) -> list[Employee]:
        result = await self._session.execute(
            select(EmployeeModel).where(
                EmployeeModel.manager_user_id == manager_user_id,
                EmployeeModel.is_active == True,  # noqa: E712
            )
        )
        return [self._to_entity(m) for m in result.scalars().all()]
