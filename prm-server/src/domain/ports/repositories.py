from abc import ABC, abstractmethod
from datetime import date

from src.domain.entities.user import User


class IUserRepository(ABC):

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        """Return User if found, None otherwise."""

    @abstractmethod
    async def find_by_id(self, user_id: int) -> User | None:
        """Return User if found, None otherwise."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist new user or update existing one. Returns saved entity."""

    @abstractmethod
    async def update_password(
        self,
        user_id: int,
        new_password_hash: str,
        force_password_change: bool,
    ) -> None:
        """Update password hash and force_password_change flag atomically."""
