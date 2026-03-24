"""
Configuration — Variables d'environnement du Log Service

📚 Explication Pédagogique :
On utilise pydantic-settings pour :
1. Charger les variables d'environnement (fichier .env ou système)
2. Valider automatiquement les types
3. Documenter la configuration

🔑 Pattern "Database per Service" :
Chaque microservice a sa PROPRE base de données.
→ log-service → PostgreSQL (log_db)
→ auth-service → PostgreSQL (auth_db)
→ booking-service → PostgreSQL (booking_db)
→ etc.

Pourquoi ?
- Isolation : un bug dans auth ne casse pas les logs
- Autonomie : chaque équipe gère son schéma
- Scalabilité : on scale la DB indépendamment
- Résilience : si une DB tombe, les autres services continuent
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration du Log Service."""

    # ── Service ──
    SERVICE_NAME: str = "log-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8005
    DEBUG: bool = False

    # ── Base de données PROPRE au log-service (Database per Service) ──
    DATABASE_URL: str = "postgresql+asyncpg://log_user:log_password@log-db:5432/log_db"
    DATABASE_ECHO: bool = False  # True pour voir les requêtes SQL (debug)

    # ── Logging ──
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" pour production, "console" pour dev

    # ── CORS (pour que les autres services puissent appeler) ──
    CORS_ORIGINS: str = "*"

    # ── Health check ──
    HEALTH_CHECK_PATH: str = "/health"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pour la configuration.
    @lru_cache évite de recharger le .env à chaque appel.
    """
    return Settings()
