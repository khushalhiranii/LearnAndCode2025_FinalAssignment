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


# --- Sprint 3 additions ---

class ProjectNotFoundError(DomainException):
    """No project found for the given identifier."""


class DuplicateProjectNameError(DomainException):
    """A project with this name already exists."""


class MilestoneNotFoundError(DomainException):
    """No milestone found for the given identifier."""


class InvalidProjectManagerError(DomainException):
    """The assigned manager is invalid (wrong role, inactive, or not found)."""


# --- Sprint 4 additions ---

class AllocationNotFoundError(DomainException):
    """No allocation found for the given identifier."""


class AllocationOverlapError(DomainException):
    """Adding this allocation would push the employee's utilization above 100%."""


class AllocationAlreadyEndedError(DomainException):
    """Cannot end an allocation that is already ended."""


class InvalidAllocationDateError(DomainException):
    """Allocation date range is invalid (from_date must be before to_date)."""


class ProjectNotActiveError(DomainException):
    """Allocations can only be made to projects with ACTIVE status."""
