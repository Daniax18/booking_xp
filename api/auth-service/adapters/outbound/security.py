from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from domain.ports.outbound import PasswordHasher, TokenProvider


# bcrypt_sha256 pre-hashes the password and avoids bcrypt 72-byte input limits.
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


class BcryptPasswordHasher(PasswordHasher):
    """Hash and verify passwords with bcrypt."""

    def hash(self, plain_password: str) -> str:
        """Return a bcrypt hash for the provided plaintext password."""
        return pwd_context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Validate a plaintext password against a bcrypt hash."""
        return pwd_context.verify(plain_password, hashed_password)


class JWTTokenProvider(TokenProvider):
    """Generate JWT access tokens for authenticated users."""

    def __init__(self, secret_key: str, algorithm: str, expire_minutes: int):
        """Store signing configuration for token creation."""
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create_access_token(self, user_id: str, email: str, role: str) -> str:
        """Build and sign a JWT containing standard user claims."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
