"""
tests/conftest.py
Configuration pyest pour les fixtures communes
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from infrastructure.databases.models import Base


@pytest.fixture
def test_client():
    """Fixture pour le client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Fixture pour une base de données de test."""
    # Utiliser SQLite en mémoire pour les tests
    SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
    
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal()
    
    Base.metadata.drop_all(bind=engine)


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
