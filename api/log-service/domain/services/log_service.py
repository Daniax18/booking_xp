"""
LogService — Service du domaine (Architecture Hexagonale)

📚 Explication Pédagogique :
Le Service du domaine est là où la LOGIQUE MÉTIER s'exécute.
Il implémente les ports inbound et utilise les ports outbound.

Flux d'une requête :
1. L'API REST (adaptateur inbound) reçoit une requête HTTP
2. Elle appelle le LogService via le port inbound
3. Le LogService exécute la logique métier
4. Il persiste via le port outbound (repository)
5. Le résultat remonte jusqu'au client

🔑 Design Patterns utilisés :
- Service Pattern : encapsule la logique métier
- Dependency Injection : les repositories sont injectés
- Observer Pattern (structlog) : notification lors de logs critiques
"""
from typing import Optional

import structlog

from domain.models.system_log import SystemLog, LogLevel
from domain.models.audit_log import AuditLog
from domain.ports.inbound import SystemLogInputPort, AuditLogInputPort
from domain.ports.outbound import SystemLogRepository, AuditLogRepository


logger = structlog.get_logger(__name__)


class LogService(SystemLogInputPort, AuditLogInputPort):
    """
    Service métier pour la gestion des logs.
    
    Ce service implémente les deux ports inbound :
    - SystemLogInputPort : gestion des logs système
    - AuditLogInputPort : gestion des logs d'audit
    
    Les repositories (ports outbound) sont injectés via le constructeur.
    C'est le principe d'Injection de Dépendances (DI).
    """

    def __init__(
        self,
        system_log_repo: SystemLogRepository,
        audit_log_repo: AuditLogRepository,
    ):
        """
        Injection de dépendances : on reçoit les repositories
        sans connaître leur implémentation concrète.
        
        On pourrait passer un PostgresRepository, un MongoRepository,
        ou un InMemoryRepository (pour les tests) — le service s'en fiche !
        """
        self._system_log_repo = system_log_repo
        self._audit_log_repo = audit_log_repo

    # ────────────────────── System Logs ──────────────────────

    async def create_system_log(
        self,
        service_name: str,
        level: LogLevel,
        message: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> SystemLog:
        """
        Créer un log système.
        
        Règles métier :
        1. Créer l'entité avec validation automatique
        2. Si le log est critique → logger une alerte
        3. Persister via le repository
        """
        # 1. Créer l'entité du domaine (validation auto dans __post_init__)
        log = SystemLog(
            service_name=service_name,
            level=level,
            message=message,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )

        # 2. Règle métier : alerter si log critique
        if log.is_critical():
            await logger.awarning(
                "🚨 Log critique détecté",
                service=service_name,
                level=level.value,
                message=message,
                correlation_id=correlation_id,
            )

        # 3. Persister
        saved_log = await self._system_log_repo.save(log)

        await logger.ainfo(
            "Log système créé",
            log_id=saved_log.id,
            service=service_name,
            level=level.value,
            correlation_id=correlation_id,
        )

        return saved_log

    async def get_system_logs(
        self,
        service_name: Optional[str] = None,
        level: Optional[LogLevel] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemLog]:
        """Récupérer les logs système avec filtres."""
        return await self._system_log_repo.find_all(
            service_name=service_name,
            level=level,
            correlation_id=correlation_id,
            limit=limit,
            offset=offset,
        )

    async def get_system_log_by_id(self, log_id: str) -> Optional[SystemLog]:
        """Récupérer un log système par ID."""
        return await self._system_log_repo.find_by_id(log_id)

    async def get_logs_by_correlation_id(self, correlation_id: str) -> list[SystemLog]:
        """
        Récupérer tous les logs d'une même requête inter-services.
        
        Cas d'usage : "Montrer tout ce qui s'est passé pour la
        réservation XYZ à travers auth → booking → payment → inventory"
        """
        return await self._system_log_repo.find_by_correlation_id(correlation_id)

    # ────────────────────── Audit Logs ──────────────────────

    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        correlation_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        """
        Créer un log d'audit.
        
        Règles métier :
        1. Créer l'entité avec validation
        2. Si action de sécurité → log spécifique
        3. Persister
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            correlation_id=correlation_id,
            details=details or {},
        )

        if log.is_security_relevant():
            await logger.awarning(
                "🔐 Action de sécurité détectée",
                user_id=user_id,
                action=action,
                entity=entity,
                correlation_id=correlation_id,
            )

        saved_log = await self._audit_log_repo.save(log)

        await logger.ainfo(
            "Log d'audit créé",
            log_id=saved_log.id,
            user_id=user_id,
            action=action,
            entity=entity,
        )

        return saved_log

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Récupérer les logs d'audit avec filtres."""
        return await self._audit_log_repo.find_all(
            user_id=user_id,
            action=action,
            entity=entity,
            limit=limit,
            offset=offset,
        )

    async def get_audit_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Récupérer un log d'audit par ID."""
        return await self._audit_log_repo.find_by_id(log_id)
