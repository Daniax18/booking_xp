from typing import Optional

from domain.models.user import User, UserStatus
from domain.ports.inbound import AuthInputPort
from domain.ports.outbound import (
    AuditLogPort,
    PasswordHasher,
    SystemLogPort,
    TokenProvider,
    UserRepository,
)


class AuthService(AuthInputPort):
    """Implement auth use cases with domain rules and outbound ports."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_provider: TokenProvider,
        audit_log_port: AuditLogPort,
        system_log_port: SystemLogPort,
    ):
        """Initialize the service with persistence, security, and logging dependencies."""
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_provider = token_provider
        self._audit_log_port = audit_log_port
        self._system_log_port = system_log_port

    async def _log_action(self, action: str, user: User, details: Optional[dict] = None) -> None:
        """Send audit and system logs without breaking the main use case on failure."""
        try:
            await self._audit_log_port.create_audit_log(
                user_id=user.id,
                action=action,
                entity="user",
                entity_id=user.id,
                details=details or {},
            )
            await self._system_log_port.create_system_log(
                level="INFO",
                message=f"auth-service called log-service for action {action}",
                metadata={
                    "user_id": user.id,
                    "email": user.email,
                    "action": action,
                },
            )
        except Exception:
            # Auth should stay available even if external log-service is down.
            return

    async def register_user(
        self,
        nom: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        """Register a user after uniqueness checks and password hashing."""
        normalized_email = email.strip().lower()
        existing = await self._user_repository.find_by_email(normalized_email)
        if existing:
            raise ValueError("Un utilisateur avec cet email existe deja")

        hashed_password = self._password_hasher.hash(password)
        user = User(
            nom=nom,
            email=normalized_email,
            password=hashed_password,
            role=role,
            status=UserStatus.ACTIVE,
        )
        saved_user = await self._user_repository.save(user)
        await self._log_action(
            action="REGISTER",
            user=saved_user,
            details={"role": saved_user.role},
        )
        return saved_user

    async def login(self, email: str, password: str) -> tuple[str, User]:
        """Authenticate credentials and return a JWT with the user."""
        normalized_email = email.strip().lower()
        user = await self._user_repository.find_by_email(normalized_email)

        if not user or not user.is_active:
            raise ValueError("Identifiants invalides")

        if not self._password_hasher.verify(password, user.password):
            raise ValueError("Identifiants invalides")

        token = self._token_provider.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )
        await self._log_action(
            action="LOGIN",
            user=user,
            details={"role": user.role},
        )
        return token, user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Return an active user by id, hiding soft-deleted users."""
        user = await self._user_repository.find_by_id(user_id)
        if user and user.status == UserStatus.DELETED:
            return None
        return user

    async def update_user(
        self,
        user_id: str,
        nom: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> User:
        """Update user profile fields with validation and uniqueness checks."""
        user = await self._user_repository.find_by_id(user_id)
        if not user or user.status == UserStatus.DELETED:
            raise ValueError("Utilisateur introuvable")

        if email:
            normalized_email = email.strip().lower()
            existing = await self._user_repository.find_by_email(normalized_email)
            if existing and existing.id != user.id:
                raise ValueError("Email deja utilise")
            user.email = normalized_email

        if nom is not None:
            cleaned_nom = nom.strip()
            if not cleaned_nom:
                raise ValueError("Le nom est obligatoire")
            user.nom = cleaned_nom

        if password:
            user.password = self._password_hasher.hash(password)

        if role:
            user.role = role.strip().lower()

        updated_user = await self._user_repository.update(user)
        await self._log_action(
            action="UPDATE",
            user=updated_user,
            details={"role": updated_user.role},
        )
        return updated_user

    async def soft_delete_user(self, user_id: str) -> User:
        """Soft delete a user by switching its status to deleted."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable")

        user.soft_delete()
        deleted_user = await self._user_repository.update(user)
        await self._log_action(
            action="DELETE",
            user=deleted_user,
            details={"status": deleted_user.status.value},
        )
        return deleted_user
