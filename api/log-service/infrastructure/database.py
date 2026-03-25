"""
Database — Connexion SQLAlchemy Async

📚 Explication Pédagogique :
On utilise SQLAlchemy avec le driver asyncpg pour PostgreSQL.
→ "async" = non-bloquant = le serveur peut traiter d'autres requêtes
  pendant qu'une requête DB attend une réponse.
→ C'est crucial pour les performances en microservices.

La session est gérée via un context manager (async with)
pour garantir la fermeture propre de la connexion.
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from infrastructure.config import get_settings


settings = get_settings()

# Moteur async — pool de connexions vers PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=10,        # Nombre de connexions maintenues
    max_overflow=20,     # Connexions supplémentaires si besoin
    pool_pre_ping=True,  # Vérifier si la connexion est vivante avant usage
)

# Factory de sessions
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe de base pour les modèles SQLAlchemy (ORM)."""
    pass


async def get_db_session() -> AsyncSession:
    """
    Générateur de session DB pour l'injection de dépendances FastAPI.
    
    Usage dans un endpoint :
        @router.get("/logs")
        async def get_logs(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Créer les tables au démarrage (utile en dev)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Fermer proprement le pool de connexions."""
    await engine.dispose()
