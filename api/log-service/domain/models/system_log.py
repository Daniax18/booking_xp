"""
SystemLog — Entité du domaine (Architecture Hexagonale)

📚 Explication Pédagogique :
- Une entité du domaine est un objet métier pur, sans dépendance à un framework.
- Elle contient la logique et les règles métier (validation, comportement).
- Le domaine est le CŒUR de l'architecture hexagonale.
- Ici, SystemLog représente un log système collecté par un microservice.

🔑 Design Pattern : Value Object (LogLevel est un Value Object via Enum)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field


class LogLevel(str, Enum):
    """
    Value Object — Niveaux de sévérité des logs.
    
    Pourquoi un Enum ?
    → Contraindre les valeurs possibles au niveau du domaine
    → Prévenir les erreurs de typo ("EROR" au lieu de "ERROR")
    → Auto-documentation du code
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SystemLog:
    """
    Entité SystemLog — Représente un log système dans la plateforme.
    
    Chaque microservice (auth, booking, payment, inventory) émet des logs
    qui sont centralisés ici pour l'observabilité.

    Attributs:
        id: Identifiant unique (UUID)
        service_name: Nom du service émetteur (ex: "auth-service")
        level: Niveau de sévérité (DEBUG → CRITICAL)
        message: Description de l'événement
        correlation_id: ID de traçabilité inter-services (très important !)
        timestamp: Horodatage de l'événement
        metadata: Données additionnelles (flexible)
    
    📌 Le correlation_id est essentiel en microservices :
    Quand un utilisateur fait une réservation, la requête traverse
    auth → booking → payment → inventory.
    Le même correlation_id permet de suivre TOUT le parcours.
    """
    service_name: str
    level: LogLevel
    message: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validation des règles métier à la création."""
        if not self.service_name:
            raise ValueError("service_name est obligatoire")
        if not self.message:
            raise ValueError("message est obligatoire")
        if isinstance(self.level, str):
            self.level = LogLevel(self.level)

    def is_critical(self) -> bool:
        """Un log critique doit déclencher une alerte."""
        return self.level in (LogLevel.ERROR, LogLevel.CRITICAL)

    def to_dict(self) -> dict:
        """Sérialisation en dictionnaire."""
        return {
            "id": self.id,
            "service_name": self.service_name,
            "level": self.level.value,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
