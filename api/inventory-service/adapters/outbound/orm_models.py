"""Modeles ORM SQLAlchemy pour la base de donnees PostgreSQL."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from infrastructure.database import Base


class ResourceORM(Base):
    """Modele ORM pour les ressources."""

    __tablename__ = 'resources'

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # HOTEL_ROOM, RESTAURANT_TABLE, VENUE
    description = Column(String(1000), nullable=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String(500), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    availability_slots = relationship('AvailabilitySlotORM', back_populates='resource', cascade='all, delete-orphan')


class AvailabilitySlotORM(Base):
    """Modele ORM pour les creneaux de disponibilite."""

    __tablename__ = 'availability_slots'

    id = Column(String, primary_key=True)
    resource_id = Column(String, ForeignKey('resources.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    quantity_available = Column(Integer, nullable=False, default=1)
    reason_if_unavailable = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship('ResourceORM', back_populates='availability_slots')
