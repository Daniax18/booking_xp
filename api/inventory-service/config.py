# config.py
"""Configuration du Inventory Service."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Configuration de la base de données."""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class LogConfig:
    """Configuration du logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None


@dataclass
class AppConfig:
    """Configuration de l'application."""
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False
    title: str = "Inventory Service"
    version: str = "1.0.0"


class Config:
    """Configuration centralisée du service."""

    # Database - PostgreSQL (asyncpg driver - asynchrone)
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://inventory_user:inventory_password@localhost:5432/inventory_db"
    )
    
    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.environ.get("LOG_FILE", None)
    
    # App
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", 8002))
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() in ("true", "1")
    
    # Environment
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    IS_PRODUCTION: bool = ENVIRONMENT == "production"
    
    # CORS
    CORS_ORIGINS: list = os.environ.get("CORS_ORIGINS", "*").split(",")
    
    @classmethod
    def get_db_config(cls) -> DatabaseConfig:
        """Récupérer la configuration de la base de données."""
        return DatabaseConfig(
            url=cls.DATABASE_URL,
            echo=not cls.IS_PRODUCTION,
            pool_size=5 if not cls.IS_PRODUCTION else 20,
            max_overflow=10 if not cls.IS_PRODUCTION else 40
        )

    @classmethod
    def get_log_config(cls) -> LogConfig:
        """Récupérer la configuration du logging."""
        return LogConfig(
            level=cls.LOG_LEVEL,
            file=cls.LOG_FILE
        )

    @classmethod
    def get_app_config(cls) -> AppConfig:
        """Récupérer la configuration de l'application."""
        return AppConfig(
            host=cls.HOST,
            port=cls.PORT,
            debug=cls.DEBUG,
        )
