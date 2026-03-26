from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from infrastructure.config import get_settings


settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class used by SQLAlchemy ORM models."""


async def get_db_session() -> AsyncSession:
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


async def init_db() -> None:
    """Create database tables at service startup."""
    from adapters.outbound import orm_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the SQLAlchemy engine on application shutdown."""
    await engine.dispose()
