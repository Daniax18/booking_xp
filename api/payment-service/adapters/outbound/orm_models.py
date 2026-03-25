"""
ORM Models — SQLAlchemy pour Payment

📚 Explication Pédagogique :
Le modèle ORM est l'adaptation entre la base de données et le domaine.
Il ne doit contenir AUCUNE logique métier, seulement la structure de table.
"""
from sqlalchemy import Column, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class PaymentORM(Base):
    """Modèle ORM pour la table payments."""
    
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True)
    booking_id = Column(String(36), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    status = Column(String(20), nullable=False, index=True)
    method = Column(String(30), nullable=False)
    refunded_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    extra_metadata = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
