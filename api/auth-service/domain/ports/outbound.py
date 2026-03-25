from abc import ABC, abstractmethod
from typing import Optional

from domain.models.user import User


class UserRepository(ABC):
    """Define persistence operations required by the auth domain."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist a new user."""
        ...

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by its identifier."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by its email address."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Persist updates for an existing user."""
        ...


class PasswordHasher(ABC):
    """Define password hashing and verification behavior."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Hash a plaintext password."""
        ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Validate a plaintext password against a hash."""
        ...


class TokenProvider(ABC):
    """Define token generation behavior used by the auth domain."""

    @abstractmethod
    def create_access_token(self, user_id: str, email: str, role: str) -> str:
        """Generate an access token for an authenticated user."""
        ...


class AuditLogPort(ABC):
    """Define how the domain sends audit events to an external system."""

    @abstractmethod
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        details: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Send an audit log event."""
        ...


class SystemLogPort(ABC):
    """Define how the domain sends technical logs to an external system."""

    @abstractmethod
    async def create_system_log(
        self,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Send a system log event."""
        ...
