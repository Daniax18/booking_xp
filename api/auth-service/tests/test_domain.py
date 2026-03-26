from datetime import datetime

import pytest

from domain.models.user import User, UserStatus
from domain.services.auth_service import AuthService


class InMemoryUserRepository:
    """Provide an in-memory fake repository for unit tests."""

    def __init__(self):
        """Initialize in-memory user storage."""
        self._users = {}

    async def save(self, user: User) -> User:
        """Store a new user in memory."""
        self._users[user.id] = user
        return user

    async def find_by_id(self, user_id: str):
        """Return one user by id from memory."""
        return self._users.get(user_id)

    async def find_by_email(self, email: str):
        """Return one user by email from memory."""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def update(self, user: User) -> User:
        """Update an existing user in memory."""
        self._users[user.id] = user
        return user


class FakePasswordHasher:
    """Provide deterministic hash behavior for tests."""

    def hash(self, plain_password: str) -> str:
        """Return a stable fake hash string."""
        return f"hashed::{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Check whether a fake hash matches the plaintext."""
        return hashed_password == f"hashed::{plain_password}"


class FakeTokenProvider:
    """Provide deterministic token generation for tests."""

    def create_access_token(self, user_id: str, email: str, role: str) -> str:
        """Return a stable fake token string."""
        return f"token::{user_id}::{email}::{role}"


class FakeAuditLogPort:
    """Capture audit log calls performed by the domain service."""

    def __init__(self):
        """Initialize call recorder."""
        self.calls = []

    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        details=None,
        correlation_id=None,
    ) -> None:
        """Record an audit log call with the provided payload."""
        self.calls.append(
            {
                "user_id": user_id,
                "action": action,
                "entity": entity,
                "entity_id": entity_id,
                "details": details or {},
                "correlation_id": correlation_id,
            }
        )


class FakeSystemLogPort:
    """Capture system log calls performed by the domain service."""

    def __init__(self):
        """Initialize call recorder."""
        self.calls = []

    async def create_system_log(
        self,
        level: str,
        message: str,
        metadata=None,
        correlation_id=None,
    ) -> None:
        """Record a system log call with the provided payload."""
        self.calls.append(
            {
                "level": level,
                "message": message,
                "metadata": metadata or {},
                "correlation_id": correlation_id,
            }
        )


@pytest.fixture
def auth_dependencies():
    """Build the service and fakes to assert behavior in tests."""
    audit_log_port = FakeAuditLogPort()
    system_log_port = FakeSystemLogPort()
    service = AuthService(
        user_repository=InMemoryUserRepository(),
        password_hasher=FakePasswordHasher(),
        token_provider=FakeTokenProvider(),
        audit_log_port=audit_log_port,
        system_log_port=system_log_port,
    )
    return service, audit_log_port, system_log_port


@pytest.mark.asyncio
async def test_register_user_success(auth_dependencies):
    """Ensure registering a user stores normalized and secured data."""
    auth_service, _, _ = auth_dependencies
    user = await auth_service.register_user(
        nom="Alice",
        email="alice@example.com",
        password="secret123",
        role="admin",
    )

    assert user.id
    assert user.nom == "Alice"
    assert user.email == "alice@example.com"
    assert user.password != "secret123"
    assert user.password.startswith("hashed::")
    assert user.role == "admin"
    assert user.status == UserStatus.ACTIVE
    assert isinstance(user.created_at, datetime)


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(auth_dependencies):
    """Ensure duplicate email registration is rejected."""
    auth_service, _, _ = auth_dependencies
    await auth_service.register_user("Alice", "alice@example.com", "secret123")

    with pytest.raises(ValueError, match="existe deja"):
        await auth_service.register_user("Bob", "alice@example.com", "secret123")


@pytest.mark.asyncio
async def test_login_returns_token(auth_dependencies):
    """Ensure valid credentials return a token and user data."""
    auth_service, _, _ = auth_dependencies
    user = await auth_service.register_user("Alice", "alice@example.com", "secret123")

    token, logged_user = await auth_service.login("alice@example.com", "secret123")

    assert token.startswith("token::")
    assert logged_user.id == user.id


@pytest.mark.asyncio
async def test_login_deleted_user_fails(auth_dependencies):
    """Ensure deleted users cannot authenticate."""
    auth_service, _, _ = auth_dependencies
    user = await auth_service.register_user("Alice", "alice@example.com", "secret123")
    await auth_service.soft_delete_user(user.id)

    with pytest.raises(ValueError, match="Identifiants invalides"):
        await auth_service.login("alice@example.com", "secret123")


@pytest.mark.asyncio
async def test_update_user(auth_dependencies):
    """Ensure updating a user persists changed fields."""
    auth_service, _, _ = auth_dependencies
    user = await auth_service.register_user("Alice", "alice@example.com", "secret123")

    updated = await auth_service.update_user(
        user_id=user.id,
        nom="Alice Doe",
        email="alice.doe@example.com",
        password="newpass123",
        role="manager",
    )

    assert updated.nom == "Alice Doe"
    assert updated.email == "alice.doe@example.com"
    assert updated.role == "manager"
    assert updated.password == "hashed::newpass123"


@pytest.mark.asyncio
async def test_soft_delete_user(auth_dependencies):
    """Ensure soft deletion hides users from standard retrieval."""
    auth_service, _, _ = auth_dependencies
    user = await auth_service.register_user("Alice", "alice@example.com", "secret123")

    deleted = await auth_service.soft_delete_user(user.id)
    fetched = await auth_service.get_user_by_id(user.id)

    assert deleted.status == UserStatus.DELETED
    assert fetched is None


@pytest.mark.asyncio
async def test_logging_is_emitted_for_each_business_action(auth_dependencies):
    """Ensure register, login, update, and delete send audit and system logs."""
    auth_service, audit_log_port, system_log_port = auth_dependencies

    user = await auth_service.register_user("Alice", "alice@example.com", "secret123")
    await auth_service.login("alice@example.com", "secret123")
    await auth_service.update_user(user.id, nom="Alice Doe")
    await auth_service.soft_delete_user(user.id)

    actions = [call["action"] for call in audit_log_port.calls]

    assert actions == ["REGISTER", "LOGIN", "UPDATE", "DELETE"]
    assert len(system_log_port.calls) == 4
    assert all(call["level"] == "INFO" for call in system_log_port.calls)
