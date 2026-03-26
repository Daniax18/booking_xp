"""
tests/conftest.py
Configuration pytest pour les fixtures communes (async)
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from httpx import AsyncClient

from infrastructure.databases.models import Base
from main import app


@pytest_asyncio.fixture
async def test_db():
    """Fixture pour une base de donnees de test asynchrone."""
    SQLALCHEMY_TEST_DATABASE_URL = 'postgresql+asyncpg://inventory_user:inventory_password@localhost:5432/inventory_test'
    engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    """Fixture pour un client de test FastAPI asynchrone."""
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client


@pytest.fixture
def sample_resource_data():
    """Fixture avec des donnees d'exemple pour une ressource hoteliere."""
    return {
        'name': 'Chambre Deluxe 201',
        'type': 'HOTEL_ROOM',
        'description': 'Chambre double avec vue mer',
        'capacity': 2,
        'location': 'Hotel UrbanHub - Etage 2',
        'price': 180.0,
    }


@pytest.fixture
def sample_availability_data():
    """Fixture avec des donnees d'exemple pour un creneau."""
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=8)
    return {
        'start_time': start.isoformat(),
        'end_time': end.isoformat(),
        'quantity': 2,
    }
