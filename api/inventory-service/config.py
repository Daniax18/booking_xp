"""Configuration d'execution de l'Inventory Service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Stocker la configuration chargee depuis les variables d'environnement."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SERVICE_NAME: str = "inventory-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8002
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+asyncpg://inventory_user:inventory_password@localhost:5432/inventory_db"
    )
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_PRE_PING: bool = True

    CORS_ORIGINS: str = "*"


@lru_cache
def get_settings() -> Settings:
    """Retourner une instance mise en cache de la configuration."""
    return Settings()
