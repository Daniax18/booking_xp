from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    SERVICE_NAME: str = 'booking-service'
    SERVICE_HOST: str = '0.0.0.0'
    SERVICE_PORT: int = 8003
    DEBUG: bool = False

    DATABASE_URL: str = 'postgresql+asyncpg://booking_user:booking_password@localhost:5433/booking_db'
    DATABASE_ECHO: bool = False

    LOG_SERVICE_URL: str = 'http://localhost:8005'
    LOG_SERVICE_TIMEOUT_SECONDS: float = 5.0

    INVENTORY_SERVICE_URL: str = 'http://localhost:8002'
    INVENTORY_SERVICE_TIMEOUT_SECONDS: float = 5.0
    INVENTORY_INTEGRATION_MODE: str = 'stub'

    PAYMENT_SERVICE_URL: str = 'http://localhost:8004'
    PAYMENT_SERVICE_TIMEOUT_SECONDS: float = 5.0
    PAYMENT_INTEGRATION_MODE: str = 'stub'

    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = 'json'
    CORS_ORIGINS: str = '*'


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
