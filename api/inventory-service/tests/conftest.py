"""
tests/conftest.py
Configuration pytest pour les fixtures communes (async)
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient

from main import app
from infrastructure.databases.models import Base


@pytest_asyncio.fixture
async def test_db():
    """Fixture pour une base de données de test asynchrone."""
    # Utiliser une PostgreSQL asyncpg pour les tests
    SQLALCHEMY_TEST_DATABASE_URL = "postgresql+asyncpg://inventory_user:inventory_password@localhost:5432/inventory_test"
    
    engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, echo=False)
    
    # Créer toutes les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    yield async_session
    
    # Nettoyer: supprimer toutes les tables après les tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    """Fixture pour un client de test FastAPI asynchrone."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_resource_data():
    """Fixture avec des données d'exemple pour une ressource."""
    return {
        "name": "Salle Test",
        "type": "room",
        "description": "Salle de réunion de test",
        "capacity": 20,
        "location": "Building A",
        "price": 100.0
    }


@pytest.fixture
def sample_availability_data():
    """Fixture avec des données d'exemple pour un créneau."""
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=8)
    
    return {
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "quantity": 2
    }
