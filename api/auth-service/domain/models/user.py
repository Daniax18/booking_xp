from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class UserStatus(str, Enum):
    """Represent supported lifecycle states for a user account."""

    ACTIVE = "active"
    DELETED = "deleted"


@dataclass
class User:
    """Represent the core user entity handled by the auth domain."""

    nom: str
    email: str
    password: str
    role: str = "user"
    status: UserStatus = UserStatus.ACTIVE
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Normalize and validate user attributes after initialization."""
        self.nom = self.nom.strip()
        self.email = self.email.strip().lower()
        self.role = self.role.strip().lower()

        if not self.nom:
            raise ValueError("Le nom est obligatoire")
        if "@" not in self.email:
            raise ValueError("Email invalide")
        if not self.password:
            raise ValueError("Le mot de passe est obligatoire")

    @property
    def is_active(self) -> bool:
        """Indicate whether the user can authenticate."""
        return self.status == UserStatus.ACTIVE

    def soft_delete(self):
        """Mark the user as deleted without removing the database record."""
        self.status = UserStatus.DELETED
