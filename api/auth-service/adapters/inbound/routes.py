from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.schemas import (
    HealthResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterUserRequest,
    UpdateUserRequest,
    UserResponse,
)
from adapters.outbound.log_service_client import HttpLogServiceClient
from adapters.outbound.repositories import PostgresUserRepository
from adapters.outbound.security import BcryptPasswordHasher, JWTTokenProvider
from domain.models.user import User
from domain.services.auth_service import AuthService
from infrastructure.config import get_settings
from infrastructure.database import get_db_session


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
# auto_error=False lets us log missing/invalid authentication attempts ourselves.
security = HTTPBearer(auto_error=False)


def _to_user_response(user: User) -> UserResponse:
    """Convert a domain user entity to the outbound API schema."""
    return UserResponse(
        id=user.id,
        nom=user.nom,
        email=user.email,
        role=user.role,
        status=user.status.value,
        created_at=user.created_at,
    )


def _build_log_client() -> HttpLogServiceClient:
    """Create a log-service client using runtime configuration."""
    settings = get_settings()
    return HttpLogServiceClient(
        base_url=settings.LOG_SERVICE_URL,
        service_name=settings.SERVICE_NAME,
        timeout_seconds=settings.LOG_SERVICE_TIMEOUT_SECONDS,
    )


async def _log_nok(
    *,
    request: Request,
    message: str,
    metadata: Optional[dict] = None,
    level: str = "WARNING",
) -> None:
    """Send a best-effort system log for unsuccessful auth flows."""
    try:
        log_client = _build_log_client()
        await log_client.create_system_log(
            level=level,
            message=message,
            metadata={
                "path": request.url.path,
                "method": request.method,
                **(metadata or {}),
            },
        )
    except Exception:
        return


def get_auth_service(db: AsyncSession) -> AuthService:
    """Build the auth service with concrete repository and security adapters."""
    settings = get_settings()
    user_repo = PostgresUserRepository(db)
    password_hasher = BcryptPasswordHasher()
    token_provider = JWTTokenProvider(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expire_minutes=settings.JWT_EXPIRE_MINUTES,
    )
    log_client = _build_log_client()
    return AuthService(
        user_repository=user_repo,
        password_hasher=password_hasher,
        token_provider=token_provider,
        audit_log_port=log_client,
        system_log_port=log_client,
    )


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Validate bearer token and return decoded JWT claims."""
    settings = get_settings()

    if credentials is None:
        await _log_nok(
            request=request,
            message="Authentication failed: missing bearer token",
            metadata={"reason": "missing_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        await _log_nok(
            request=request,
            message="Authentication failed: invalid or expired token",
            metadata={"reason": "invalid_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expire",
        ) from exc

    subject = payload.get("sub")
    if not subject:
        await _log_nok(
            request=request,
            message="Authentication failed: token missing subject claim",
            metadata={"reason": "missing_sub_claim"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: claim 'sub' manquant",
        )

    return payload


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    request_body: RegisterUserRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new user account."""
    service = get_auth_service(db)
    try:
        user = await service.register_user(
            nom=request_body.nom,
            email=request_body.email,
            password=request_body.password,
            role=request_body.role,
        )
    except ValueError as exc:
        await _log_nok(
            request=request,
            message="Register failed",
            metadata={"email": request_body.email, "reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        await _log_nok(
            request=request,
            message="Register failed unexpectedly",
            metadata={"email": request_body.email, "reason": str(exc)},
            level="ERROR",
        )
        raise

    return _to_user_response(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    request_body: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Authenticate a user and return an access token."""
    service = get_auth_service(db)
    try:
        token, user = await service.login(
            email=request_body.email,
            password=request_body.password,
        )
    except ValueError as exc:
        await _log_nok(
            request=request,
            message="Login failed",
            metadata={"email": request_body.email, "reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except Exception as exc:
        await _log_nok(
            request=request,
            message="Login failed unexpectedly",
            metadata={"email": request_body.email, "reason": str(exc)},
            level="ERROR",
        )
        raise

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_response(user),
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    claims: dict = Depends(require_auth),
):
    """Retrieve one active user by its identifier."""
    _ = claims
    service = get_auth_service(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        await _log_nok(
            request=request,
            message="Get user failed",
            metadata={"user_id": user_id, "reason": "not_found"},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    return _to_user_response(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: str,
    request_body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db_session),
    claims: dict = Depends(require_auth),
):
    """Update mutable fields of an existing user."""
    _ = claims
    service = get_auth_service(db)
    try:
        user = await service.update_user(
            user_id=user_id,
            nom=request_body.nom,
            email=request_body.email,
            password=request_body.password,
            role=request_body.role,
        )
    except ValueError as exc:
        message = str(exc)
        await _log_nok(
            request=request,
            message="Update failed",
            metadata={"user_id": user_id, "reason": message},
        )
        error_code = status.HTTP_404_NOT_FOUND if message == "Utilisateur introuvable" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=error_code, detail=message) from exc
    except Exception as exc:
        await _log_nok(
            request=request,
            message="Update failed unexpectedly",
            metadata={"user_id": user_id, "reason": str(exc)},
            level="ERROR",
        )
        raise

    return _to_user_response(user)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def soft_delete_user(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    claims: dict = Depends(require_auth),
):
    """Soft delete a user by changing its status."""
    _ = claims
    service = get_auth_service(db)
    try:
        await service.soft_delete_user(user_id)
    except ValueError as exc:
        await _log_nok(
            request=request,
            message="Delete failed",
            metadata={"user_id": user_id, "reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        await _log_nok(
            request=request,
            message="Delete failed unexpectedly",
            metadata={"user_id": user_id, "reason": str(exc)},
            level="ERROR",
        )
        raise

    return MessageResponse(message="Utilisateur supprime (soft delete)")


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Check API and database health status."""
    try:
        await db.execute(text("SELECT 1"))
        status_value = "healthy"
    except Exception:
        status_value = "degraded"

    return HealthResponse(status=status_value, service="auth-service")
