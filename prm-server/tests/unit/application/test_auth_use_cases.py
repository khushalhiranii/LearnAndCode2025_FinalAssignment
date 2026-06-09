import pytest

from src.application.auth.change_password_use_case import ChangePasswordUseCase
from src.application.auth.login_use_case import LoginUseCase
from src.application.dtos.auth_dtos import (
    ChangePasswordRequest,
    PasswordChangeRequiredResponse,
    LoginRequest,
    LoginResponse,
)
from src.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from src.infrastructure.security.password_hasher import verify_password
from tests.conftest import InMemoryUserRepository


# ── LoginUseCase ──────────────────────────────────────────────────────────────


class TestLoginUseCaseValidCredentials:
    """Valid credentials, no force change → returns access token."""

    async def test_returns_login_response(
        self, active_admin_user: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(active_admin_user)
        result = await uc.execute(LoginRequest(username="admin", password="Admin@1234"))
        assert isinstance(result, LoginResponse)
        assert result.access_token != ""
        assert result.role == "ADMIN"

    async def test_token_type_is_bearer(
        self, active_admin_user: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(active_admin_user)
        result = await uc.execute(LoginRequest(username="admin", password="Admin@1234"))
        assert isinstance(result, LoginResponse)
        assert result.token_type == "bearer"


class TestLoginUseCaseWrongPassword:
    """Wrong password → InvalidCredentialsError."""

    async def test_raises_invalid_credentials(
        self, active_admin_user: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(active_admin_user)
        with pytest.raises(InvalidCredentialsError):
            await uc.execute(LoginRequest(username="admin", password="WrongPass@1"))


class TestLoginUseCaseUnknownUsername:
    """Non-existent username → InvalidCredentialsError (same error, no user enumeration)."""

    async def test_raises_invalid_credentials(
        self, fake_user_repo: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(fake_user_repo)
        with pytest.raises(InvalidCredentialsError):
            await uc.execute(LoginRequest(username="nobody", password="Any@Pass1"))


class TestLoginUseCaseInactiveUser:
    """Deactivated user → InactiveUserError."""

    async def test_raises_inactive_user(
        self, inactive_admin: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(inactive_admin)
        with pytest.raises(InactiveUserError):
            await uc.execute(LoginRequest(username="admin", password="Admin@1234"))


class TestLoginUseCaseForcePasswordChange:
    """force_password_change=True → PasswordChangeRequiredResponse with temp token."""

    async def test_returns_change_required(
        self, force_change_admin: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(force_change_admin)
        result = await uc.execute(LoginRequest(username="admin", password="Admin@1234"))
        assert isinstance(result, PasswordChangeRequiredResponse)
        assert result.status == "PASSWORD_CHANGE_REQUIRED"
        assert result.temp_token != ""

    async def test_no_access_token_field_in_change_required(
        self, force_change_admin: InMemoryUserRepository
    ) -> None:
        uc = LoginUseCase(force_change_admin)
        result = await uc.execute(LoginRequest(username="admin", password="Admin@1234"))
        assert not hasattr(result, "access_token")


# ── ChangePasswordUseCase ─────────────────────────────────────────────────────


class TestChangePasswordUseCase:

    async def test_updates_password_and_clears_flag(
        self, force_change_admin: InMemoryUserRepository
    ) -> None:
        uc = ChangePasswordUseCase(force_change_admin)
        req = ChangePasswordRequest(new_password="NewPass@99", confirm_password="NewPass@99")
        result = await uc.execute(user_id=1, request=req)
        assert result.access_token != ""
        assert result.role == "ADMIN"

        updated = await force_change_admin.find_by_id(1)
        assert updated is not None
        assert updated.force_password_change is False

    async def test_old_password_no_longer_valid_after_change(
        self, force_change_admin: InMemoryUserRepository
    ) -> None:
        uc = ChangePasswordUseCase(force_change_admin)
        req = ChangePasswordRequest(new_password="NewPass@99", confirm_password="NewPass@99")
        await uc.execute(user_id=1, request=req)
        user = await force_change_admin.find_by_id(1)
        assert user is not None
        assert not verify_password("Admin@1234", user.password_hash)
        assert verify_password("NewPass@99", user.password_hash)

    async def test_raises_for_unknown_user_id(
        self, fake_user_repo: InMemoryUserRepository
    ) -> None:
        uc = ChangePasswordUseCase(fake_user_repo)
        req = ChangePasswordRequest(new_password="NewPass@99", confirm_password="NewPass@99")
        with pytest.raises(UserNotFoundError):
            await uc.execute(user_id=999, request=req)


# ── ChangePasswordRequest Pydantic validation ─────────────────────────────────


class TestChangePasswordRequestValidation:

    def test_rejects_short_password(self) -> None:
        with pytest.raises(Exception):
            ChangePasswordRequest(new_password="Ab1!", confirm_password="Ab1!")

    def test_rejects_no_uppercase(self) -> None:
        with pytest.raises(Exception):
            ChangePasswordRequest(new_password="password@1", confirm_password="password@1")

    def test_rejects_no_digit(self) -> None:
        with pytest.raises(Exception):
            ChangePasswordRequest(new_password="Password@!", confirm_password="Password@!")

    def test_rejects_no_special_char(self) -> None:
        with pytest.raises(Exception):
            ChangePasswordRequest(new_password="Password1", confirm_password="Password1")

    def test_rejects_mismatched_passwords(self) -> None:
        with pytest.raises(Exception):
            ChangePasswordRequest(
                new_password="Valid@Pass1", confirm_password="Different@1"
            )

    def test_accepts_valid_password(self) -> None:
        req = ChangePasswordRequest(
            new_password="Valid@Pass1", confirm_password="Valid@Pass1"
        )
        assert req.new_password == "Valid@Pass1"
