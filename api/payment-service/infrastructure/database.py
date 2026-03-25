"""
Database Setup — Initialisation SQLAlchemy & Alembic

📚 Explication Pédagogique :
La couche database :
1. Crée le moteur async PostgreSQL
2. Configure les sessionsasync
3. Initialise les tables (DDL)
4. Gère le cycle de vie (ouverture/fermeture de connexions)
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from infrastructure.config import get_settings
from adapters.outbound.orm_models import Base


# Moteur async global
_engine = None
_async_session_maker = None


async def init_db():
    """Initialiser la base de données."""
    global _engine, _async_session_maker
    
    settings = get_settings()
    
    try:
        # Créer le moteur async
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            poolclass=NullPool,  # Pour éviter les fuites de connexions
        )
        
        # Créer le session factory
        _async_session_maker = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Créer les tables
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        import structlog
        logger = structlog.get_logger(__name__)
        logger.info("✅ Database initialized successfully", database_url=settings.DATABASE_URL)
    
    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error(
            "⚠️ Database connection failed (will run in degraded mode)",
            error=str(e),
            database_url=settings.DATABASE_URL,
        )
        # Ne pas lever l'exception - laisser l'app démarrer en mode dégradé
        # Les endpoints qui ont besoin de la DB feront fail proprement


async def close_db():
    """Fermer la base de données."""
    global _engine
    if _engine:
        await _engine.dispose()


async def get_db_session() -> AsyncSession:
    """Obtenir une session SQLAlchemy pour injection de dépendances."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized")
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
