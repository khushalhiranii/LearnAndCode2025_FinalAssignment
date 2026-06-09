from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.domain.enums import Role


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    role: Role


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: Role
    is_active: bool
    force_password_change: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class DeactivateUserRequest(BaseModel):
    reason: str | None = None


class ReactivateUserRequest(BaseModel):
    pass


class ResetPasswordResponse(BaseModel):
    temp_password: str
    message: str = "Temporary password set. User must change password on next login."
