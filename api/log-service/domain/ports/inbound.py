"""
Inbound Ports (Driving Ports) — Cas d'utilisation

📚 Ces interfaces définissent CE QUE le domaine SAIT FAIRE.
Les adaptateurs inbound (ex: API REST) appellent ces ports.

🔑 Design Pattern : Interface Segregation Principle (ISP) du SOLID
→ Chaque port a une responsabilité claire et limitée
"""
from abc import ABC, abstractmethod
from typing import Optional

from domain.models.system_log import SystemLog, LogLevel
from domain.models.audit_log import AuditLog


class SystemLogInputPort(ABC):
    """
    Port d'entrée pour la gestion des logs système.
    
    C'est par ici que l'API REST (adaptateur inbound) communique
    avec le domaine pour créer et consulter des logs système.
    """

    @abstractmethod
    async def create_system_log(
        self,
        service_name: str,
        level: LogLevel,
        message: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> SystemLog:
        """Créer un nouveau log système."""
        ...

    @abstractmethod
    async def get_system_logs(
        self,
        service_name: Optional[str] = None,
        level: Optional[LogLevel] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemLog]:
        """Récupérer les logs système avec filtres optionnels."""
        ...

    @abstractmethod
    async def get_system_log_by_id(self, log_id: str) -> Optional[SystemLog]:
        """Récupérer un log système par son ID."""
        ...

    @abstractmethod
    async def get_logs_by_correlation_id(self, correlation_id: str) -> list[SystemLog]:
        """
        Récupérer tous les logs liés à un même correlation_id.
        
        Très utile pour tracer le parcours complet d'une requête
        à travers tous les microservices.
        """
        ...


class AuditLogInputPort(ABC):
    """
    Port d'entrée pour la gestion des logs d'audit.
    """

    @abstractmethod
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        correlation_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        """Créer un nouveau log d'audit."""
        ...

    @abstractmethod
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Récupérer les logs d'audit avec filtres."""
        ...

    @abstractmethod
    async def get_audit_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Récupérer un log d'audit par son ID."""
        ...
