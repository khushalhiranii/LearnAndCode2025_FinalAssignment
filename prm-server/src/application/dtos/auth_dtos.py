import re

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    """Returned on successful login (force_password_change = False)."""

    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class PasswordChangeRequiredResponse(BaseModel):
    """Returned when force_password_change = True. Client must call change-password."""

    status: str = "PASSWORD_CHANGE_REQUIRED"
    temp_token: str


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must contain at least one special character.")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class ChangePasswordResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
