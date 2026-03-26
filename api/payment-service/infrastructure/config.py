"""
Configuration — Variables d'environnement

📚 Explication Pédagogique :
Toute la configuration vient de l'environnement (12-factor app).
Pas de hardcoding, tout est pydantic + env vars.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration du payment-service."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Service
    SERVICE_NAME: str = "payment-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8004
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://payment_user:payment_password@localhost:5434/payment_db"
    DATABASE_ECHO: bool = False
    
    # Log Service
    LOG_SERVICE_URL: str = "http://localhost:8005"
    LOG_SERVICE_TIMEOUT_SECONDS: float = 5.0
    
    # CORS
    CORS_ORIGINS: str = "*"


@lru_cache
def get_settings() -> Settings:
    """Retourner une instance cached de Settings."""
    return Settings()
