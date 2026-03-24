"""
Outbound Ports (Driven Ports) — Interfaces vers l'extérieur

📚 Ces interfaces définissent CE DONT le domaine A BESOIN.
Les adaptateurs outbound (ex: PostgreSQL Repository) implémentent ces ports.

🔑 Design Pattern : Repository Pattern
→ Le domaine ne sait pas comment les données sont stockées
→ Il sait juste qu'il peut save() et find() via le port
→ L'adaptateur outbound décide du COMMENT (PostgreSQL, MongoDB, fichier, etc.)

C'est le principe d'Inversion de Dépendance (DIP du SOLID) :
Le domaine définit l'interface, l'infrastructure l'implémente.
"""
from abc import ABC, abstractmethod
from typing import Optional

from domain.models.system_log import SystemLog, LogLevel
from domain.models.audit_log import AuditLog


class SystemLogRepository(ABC):
    """
    Repository Pattern pour SystemLog.
    
    Interface que doit implémenter tout adaptateur de persistance
    pour les logs système.
    """

    @abstractmethod
    async def save(self, log: SystemLog) -> SystemLog:
        """Persister un log système."""
        ...

    @abstractmethod
    async def find_by_id(self, log_id: str) -> Optional[SystemLog]:
        """Trouver un log par son ID."""
        ...

    @abstractmethod
    async def find_all(
        self,
        service_name: Optional[str] = None,
        level: Optional[LogLevel] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemLog]:
        """Trouver les logs avec filtres."""
        ...

    @abstractmethod
    async def find_by_correlation_id(self, correlation_id: str) -> list[SystemLog]:
        """Trouver tous les logs d'une même corrélation."""
        ...

    @abstractmethod
    async def count(
        self,
        service_name: Optional[str] = None,
        level: Optional[LogLevel] = None,
    ) -> int:
        """Compter les logs avec filtres."""
        ...


class AuditLogRepository(ABC):
    """
    Repository Pattern pour AuditLog.
    """

    @abstractmethod
    async def save(self, log: AuditLog) -> AuditLog:
        """Persister un log d'audit."""
        ...

    @abstractmethod
    async def find_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Trouver un log d'audit par son ID."""
        ...

    @abstractmethod
    async def find_all(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Trouver les logs d'audit avec filtres."""
        ...

    @abstractmethod
    async def count(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> int:
        """Compter les logs d'audit avec filtres."""
        ...
