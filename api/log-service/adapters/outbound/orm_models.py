"""
ORM Models — Modèles SQLAlchemy (Adaptateur Outbound)

📚 Explication Pédagogique :
Ces modèles sont les modèles ORM (Object-Relational Mapping).
Ils sont DIFFÉRENTS des modèles du domaine !

Pourquoi séparer ?
- Les modèles du domaine sont des objets métier purs (dataclass)
- Les modèles ORM sont liés à la base de données (SQLAlchemy)
- Le domaine ne doit JAMAIS dépendre de l'infrastructure

Le mapping domaine ↔ ORM se fait dans le repository.
C'est le pattern "Anti-Corruption Layer" de DDD.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB

from infrastructure.database import Base


class SystemLogORM(Base):
    """Table 'system_logs' — Stockage des logs système."""

    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String(100), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    correlation_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSONB, nullable=True, default=dict)

    def __repr__(self):
        return f"<SystemLog {self.id} [{self.level}] {self.service_name}>"


class AuditLogORM(Base):
    """Table 'audit_logs' — Stockage des logs d'audit."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    entity = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False)
    correlation_id = Column(String(36), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    details = Column(JSONB, nullable=True, default=dict)

    def __repr__(self):
        return f"<AuditLog {self.id} [{self.action}] {self.entity}>"
