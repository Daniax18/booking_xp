# infrastructure/database.py
"""Configuration de la base de données async avec SQLAlchemy."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import Settings

# Instance de configuration
settings = Settings()

# Base pour les modèles ORM
Base = declarative_base()

# Engine async
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
)

# Session factory async
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Yield a transactional async database session for request scope."""
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
    """Initialiser la base de données (créer les tables)."""
    # Import les modèles ORM pour enregistrer la métadata
    # NOTE: Les modèles ORM doivent importer Base depuis ce module
    from adapters.outbound.orm_models import ResourceORM, AvailabilitySlotORM  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Fermer la connexion à la base de données."""
    await engine.dispose()
