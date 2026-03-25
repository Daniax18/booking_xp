from abc import ABC, abstractmethod
from typing import Optional

from domain.models.user import User


class AuthInputPort(ABC):
    """Define use cases exposed by the auth domain to driving adapters."""

    @abstractmethod
    async def register_user(
        self,
        nom: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        """Create a new user account."""
        ...

    @abstractmethod
    async def login(self, email: str, password: str) -> tuple[str, User]:
        """Authenticate a user and return an access token with user data."""
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve an active user by identifier."""
        ...

    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        nom: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> User:
        """Update mutable fields for an existing user."""
        ...

    @abstractmethod
    async def soft_delete_user(self, user_id: str) -> User:
        """Soft delete a user account by setting its status."""
        ...
