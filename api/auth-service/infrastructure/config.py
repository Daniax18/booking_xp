from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SERVICE_NAME: str = "auth-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8001
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://auth_user:auth_password@localhost:5431/auth_db"
    DATABASE_ECHO: bool = False

    LOG_SERVICE_URL: str = "http://localhost:8005"
    LOG_SERVICE_TIMEOUT_SECONDS: float = 5.0

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "*"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
