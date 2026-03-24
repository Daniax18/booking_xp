"""
PostgreSQL Repository — Adaptateur Outbound (Architecture Hexagonale)

📚 Explication Pédagogique :
Cet adaptateur IMPLÉMENTE les ports outbound (Repository interfaces).
Il contient le code concret pour interagir avec PostgreSQL.

Le domaine ne sait pas que PostgreSQL est utilisé !
Il appelle juste repo.save(log) et repo.find_by_id(id).

C'est ici qu'on fait le MAPPING entre :
- Domaine (SystemLog dataclass) ↔ ORM (SystemLogORM SQLAlchemy)

🔑 Design Pattern : Repository Pattern
→ Encapsule la logique d'accès aux données
→ Le domaine manipule des objets métier, pas des requêtes SQL
"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.system_log import SystemLog, LogLevel
from domain.models.audit_log import AuditLog
from domain.ports.outbound import SystemLogRepository, AuditLogRepository
from adapters.outbound.orm_models import SystemLogORM, AuditLogORM


class PostgresSystemLogRepository(SystemLogRepository):
    """
    Implémentation PostgreSQL du repository SystemLog.
    
    Rôle : traduire les opérations métier en requêtes SQL.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # ── Mapping Domaine ↔ ORM ──

    def _to_orm(self, log: SystemLog) -> SystemLogORM:
        """Convertir une entité du domaine en modèle ORM."""
        return SystemLogORM(
            id=log.id,
            service_name=log.service_name,
            level=log.level.value,
            message=log.message,
            correlation_id=log.correlation_id,
            timestamp=log.timestamp,
            metadata_=log.metadata,
        )

    def _to_domain(self, orm: SystemLogORM) -> SystemLog:
        """Convertir un modèle ORM en entité du domaine."""
        return SystemLog(
            id=orm.id,
            service_name=orm.service_name,
            level=LogLevel(orm.level),
            message=orm.message,
            correlation_id=orm.correlation_id,
            timestamp=orm.timestamp,
            metadata=orm.metadata_ or {},
        )

    # ── Opérations CRUD ──

    async def save(self, log: SystemLog) -> SystemLog:
        """Persister un log système dans PostgreSQL."""
        orm_log = self._to_orm(log)
        self._session.add(orm_log)
        await self._session.flush()  # Obtenir l'ID sans commiter
        return self._to_domain(orm_log)

    async def find_by_id(self, log_id: str) -> Optional[SystemLog]:
        """Trouver un log par son ID."""
        result = await self._session.get(SystemLogORM, log_id)
        return self._to_domain(result) if result else None

    async def find_all(
        self,
        service_name: Optional[str] = None,
        level: Optional[LogLevel] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemLog]:
        """Trouver les logs avec filtres optionnels."""
        query = select(SystemLogORM)

        if service_name:
            query = query.where(SystemLogORM.service_name == service_name)
        if level:
            query = query.where(SystemLogORM.level == level.value)
        if correlation_id:
            query = query.where(SystemLogORM.correlation_id == correlation_id)

        query = query.order_by(SystemLogORM.timestamp.desc())
        query = query.limit(limit).offset(offset)

        result = await self._session.execute(query)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def find_by_correlation_id(self, correlation_id: str) -> list[SystemLog]:
        """Trouver tous les logs d'une même corrélation."""
        query = (
            select(SystemLogORM)
            .where(SystemLogORM.correlation_id == correlation_id)
            .order_by(SystemLogORM.timestamp.asc())
        )
        result = await self._session.execute(query)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def count(
        self,
        service_name: Optional[str] = None,
        level: Optional[LogLevel] = None,
    ) -> int:
        """Compter les logs avec filtres."""
        query = select(func.count(SystemLogORM.id))
        if service_name:
            query = query.where(SystemLogORM.service_name == service_name)
        if level:
            query = query.where(SystemLogORM.level == level.value)
        result = await self._session.execute(query)
        return result.scalar_one()


class PostgresAuditLogRepository(AuditLogRepository):
    """
    Implémentation PostgreSQL du repository AuditLog.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_orm(self, log: AuditLog) -> AuditLogORM:
        return AuditLogORM(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            entity=log.entity,
            entity_id=log.entity_id,
            correlation_id=log.correlation_id,
            timestamp=log.timestamp,
            details=log.details,
        )

    def _to_domain(self, orm: AuditLogORM) -> AuditLog:
        return AuditLog(
            id=orm.id,
            user_id=orm.user_id,
            action=orm.action,
            entity=orm.entity,
            entity_id=orm.entity_id,
            correlation_id=orm.correlation_id,
            timestamp=orm.timestamp,
            details=orm.details or {},
        )

    async def save(self, log: AuditLog) -> AuditLog:
        orm_log = self._to_orm(log)
        self._session.add(orm_log)
        await self._session.flush()
        return self._to_domain(orm_log)

    async def find_by_id(self, log_id: str) -> Optional[AuditLog]:
        result = await self._session.get(AuditLogORM, log_id)
        return self._to_domain(result) if result else None

    async def find_all(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        query = select(AuditLogORM)

        if user_id:
            query = query.where(AuditLogORM.user_id == user_id)
        if action:
            query = query.where(AuditLogORM.action == action)
        if entity:
            query = query.where(AuditLogORM.entity == entity)

        query = query.order_by(AuditLogORM.timestamp.desc())
        query = query.limit(limit).offset(offset)

        result = await self._session.execute(query)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def count(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> int:
        query = select(func.count(AuditLogORM.id))
        if user_id:
            query = query.where(AuditLogORM.user_id == user_id)
        if action:
            query = query.where(AuditLogORM.action == action)
        result = await self._session.execute(query)
        return result.scalar_one()
