"""Response models mirroring the server's DTOs."""

from __future__ import annotations

from pydantic import BaseModel


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class PasswordChangeRequiredResponse(BaseModel):
    status: str
    temp_token: str


class ChangePasswordResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
