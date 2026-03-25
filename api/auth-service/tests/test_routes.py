from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from adapters.inbound import routes as routes_module
from adapters.inbound.routes import router
from domain.models.user import User
from infrastructure.config import get_settings
from infrastructure.database import get_db_session


class DummyAuthService:
    """Provide deterministic auth use case behavior for route tests."""

    def __init__(self):
        """Initialize fake service state used by tests."""
        self.should_fail_register = False
        self.should_fail_login = False
        self.should_fail_update = False
        self.should_fail_delete = False
        self.user = User(
            id="u-1",
            nom="Alice",
            email="alice@example.com",
            password="hashed",
            role="user",
            created_at=datetime.utcnow(),
        )

    async def register_user(self, nom: str, email: str, password: str, role: str = "user") -> User:
        """Return a fake user or raise a validation error."""
        if self.should_fail_register:
            raise ValueError("register failed")
        self.user.nom = nom
        self.user.email = email
        self.user.role = role
        return self.user

    async def login(self, email: str, password: str) -> tuple[str, User]:
        """Return a fake token or raise an authentication error."""
        if self.should_fail_login:
            raise ValueError("Identifiants invalides")
        return "token-123", self.user

    async def get_user_by_id(self, user_id: str):
        """Return the fake user or none when id differs."""
        if user_id != self.user.id:
            return None
        return self.user

    async def update_user(self, user_id: str, nom=None, email=None, password=None, role=None) -> User:
        """Return updated fake user or raise when configured."""
        if self.should_fail_update:
            raise ValueError("Utilisateur introuvable")
        if nom:
            self.user.nom = nom
        if email:
            self.user.email = email
        if role:
            self.user.role = role
        return self.user

    async def soft_delete_user(self, user_id: str) -> User:
        """Return deleted fake user or raise when configured."""
        if self.should_fail_delete:
            raise ValueError("Utilisateur introuvable")
        return self.user


@pytest.fixture
def test_app(monkeypatch):
    """Build a minimal FastAPI app with dependency overrides for route tests."""
    app = FastAPI()
    app.include_router(router)

    async def fake_db_session():
        """Yield a placeholder db dependency."""
        yield None

    app.dependency_overrides[get_db_session] = fake_db_session

    service = DummyAuthService()
    monkeypatch.setattr(routes_module, "get_auth_service", lambda db: service)

    async def noop_log_nok(**kwargs):
        """Disable external logging side effects for route tests."""
        return None

    monkeypatch.setattr(routes_module, "_log_nok", noop_log_nok)
    return app, service


def _make_token() -> str:
    """Create a valid token for protected route tests."""
    settings = get_settings()
    return jwt.encode(
        {"sub": "u-1", "email": "alice@example.com", "role": "user"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def test_register_success(test_app):
    """Ensure register endpoint returns 201 on success."""
    app, _ = test_app
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/register",
        json={"nom": "Alice", "email": "alice@example.com", "password": "admin123", "role": "user"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"


def test_register_failure_returns_400(test_app):
    """Ensure register endpoint maps domain errors to HTTP 400."""
    app, service = test_app
    service.should_fail_register = True
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/register",
        json={"nom": "Alice", "email": "alice@example.com", "password": "admin123", "role": "user"},
    )

    assert response.status_code == 400


def test_login_success(test_app):
    """Ensure login endpoint returns a bearer token on success."""
    app, _ = test_app
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "admin123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_failure_returns_401(test_app):
    """Ensure login endpoint maps auth failures to HTTP 401."""
    app, service = test_app
    service.should_fail_login = True
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "bad"},
    )

    assert response.status_code == 401


def test_get_user_requires_token_and_logs_nok(test_app, monkeypatch):
    """Ensure protected routes reject missing token and trigger NOK logging."""
    app, _ = test_app
    client = TestClient(app)

    called = {"count": 0}

    async def capture_log_nok(**kwargs):
        """Capture NOK log attempts for assertions."""
        called["count"] += 1

    monkeypatch.setattr(routes_module, "_log_nok", capture_log_nok)

    response = client.get("/api/v1/auth/users/u-1")

    assert response.status_code == 401
    assert called["count"] == 1


def test_get_user_success_with_token(test_app):
    """Ensure protected route succeeds with a valid bearer token."""
    app, _ = test_app
    client = TestClient(app)
    token = _make_token()

    response = client.get("/api/v1/auth/users/u-1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == "u-1"


def test_update_user_success(test_app):
    """Ensure update endpoint works with authentication."""
    app, _ = test_app
    client = TestClient(app)
    token = _make_token()

    response = client.put(
        "/api/v1/auth/users/u-1",
        headers={"Authorization": f"Bearer {token}"},
        json={"nom": "Alice Doe"},
    )

    assert response.status_code == 200
    assert response.json()["nom"] == "Alice Doe"


def test_delete_user_success(test_app):
    """Ensure delete endpoint works with authentication."""
    app, _ = test_app
    client = TestClient(app)
    token = _make_token()

    response = client.delete("/api/v1/auth/users/u-1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
