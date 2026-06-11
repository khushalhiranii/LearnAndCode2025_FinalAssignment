from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.enums import ProficiencyLevel


class UpdateEmployeeRequest(BaseModel):
    department: str | None = Field(None, max_length=100)
    designation: str | None = Field(None, max_length=100)
    date_of_joining: date | None = None


class AssignManagerRequest(BaseModel):
    manager_user_id: int


class AddSkillRequest(BaseModel):
    skill_id: int
    proficiency: ProficiencyLevel


class UpdateSkillRequest(BaseModel):
    proficiency: ProficiencyLevel


class CreateSkillRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)


class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    created_at: datetime
    updated_at: datetime


class EmployeeSkillResponse(BaseModel):
    id: int
    resource_profile_id: int
    skill_id: int
    skill_name: str
    proficiency: ProficiencyLevel
    created_at: datetime
    updated_at: datetime

    # Backward-compat alias consumed by serializer only — callers should use resource_profile_id
    @property
    def employee_id(self) -> int:
        return self.resource_profile_id


class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    department: str | None
    designation: str | None
    date_of_joining: date | None
    manager_user_id: int | None
    is_available: bool
    created_at: datetime
    updated_at: datetime


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    total: int
    page: int
    page_size: int
