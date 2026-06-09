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


# --- Sprint 2 additions ---

class EmployeeNotFoundError(DomainException):
    """No employee record found for the given identifier."""


class EmployeeAlreadyExistsError(DomainException):
    """An employee profile already exists for this user."""


class SkillNotFoundError(DomainException):
    """No skill found for the given identifier."""


class DuplicateSkillError(DomainException):
    """Employee already has this skill assigned."""


class InvalidManagerError(DomainException):
    """The proposed manager is invalid (wrong role, inactive, or is the same user)."""


class CannotDeactivateSelfError(DomainException):
    """Admin cannot deactivate their own account."""


class DuplicateUsernameError(DomainException):
    """A user with this username already exists."""


class DuplicateEmailError(DomainException):
    """A user with this email already exists."""
