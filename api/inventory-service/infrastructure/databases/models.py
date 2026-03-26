from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ResourceModel(Base):
    """Modele de base de donnees pour les ressources."""

    __tablename__ = 'resources'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # HOTEL_ROOM, RESTAURANT_TABLE, VENUE
    description = Column(String, nullable=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AvailabilitySlotModel(Base):
    """Modele de base de donnees pour les creneaux de disponibilite."""

    __tablename__ = 'availability_slots'

    id = Column(String, primary_key=True)
    resource_id = Column(String, ForeignKey('resources.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    quantity_available = Column(Integer, nullable=False, default=1)
    reason_if_unavailable = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
