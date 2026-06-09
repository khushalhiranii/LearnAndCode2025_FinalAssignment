class DomainException(Exception):
    """Base for all domain-level errors."""


class InvalidCredentialsError(DomainException):
    """Username not found or password does not match."""


class InactiveUserError(DomainException):
    """User account has been deactivated."""


class PasswordChangeRequiredError(DomainException):
    """Login succeeded but force_password_change is True."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__("Password change required before proceeding.")


class WeakPasswordError(DomainException):
    """Password does not meet complexity requirements."""


class UserNotFoundError(DomainException):
    """No user found for the given identifier."""


class AuthorizationError(DomainException):
    """Caller does not have permission for the requested operation."""
