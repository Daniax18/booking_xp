"""
AuditLog — Entité du domaine (Architecture Hexagonale)

📚 Explication Pédagogique :
- AuditLog trace les ACTIONS des utilisateurs (qui a fait quoi, sur quel objet).
- C'est différent de SystemLog qui trace les ÉVÉNEMENTS techniques.
- Exemple : "L'utilisateur X a CRÉÉ une réservation Y" → AuditLog
- Exemple : "Le service booking a démarré sur le port 8003" → SystemLog

🔑 Design Pattern : Entity (identité propre via UUID)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class AuditLog:
    """
    Entité AuditLog — Trace d'audit des actions utilisateur.

    Indispensable pour :
    → La conformité (RGPD, traçabilité)
    → Le debugging ("qui a modifié cette réservation ?")
    → La sécurité ("tentatives de connexion suspectes")

    Attributs:
        id: Identifiant unique
        user_id: ID de l'utilisateur ayant effectué l'action
        action: Type d'action (CREATE, UPDATE, DELETE, LOGIN, LOGOUT...)
        entity: Nom de l'entité affectée (Booking, Payment, User...)
        entity_id: ID de l'entité affectée
        correlation_id: ID de traçabilité inter-services
        timestamp: Horodatage
        details: Détails supplémentaires (ancien/nouveau état, etc.)
    """
    user_id: str
    action: str
    entity: str
    entity_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict = field(default_factory=dict)

    # Actions standards (constantes)
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_LOGIN = "LOGIN"
    ACTION_LOGOUT = "LOGOUT"
    ACTION_VIEW = "VIEW"

    VALID_ACTIONS = {
        ACTION_CREATE, ACTION_UPDATE, ACTION_DELETE,
        ACTION_LOGIN, ACTION_LOGOUT, ACTION_VIEW
    }

    def __post_init__(self):
        """Validation des règles métier."""
        if not self.user_id:
            raise ValueError("user_id est obligatoire")
        if not self.action:
            raise ValueError("action est obligatoire")
        if not self.entity:
            raise ValueError("entity est obligatoire")

    def is_security_relevant(self) -> bool:
        """Détermine si l'action est liée à la sécurité."""
        return self.action in (self.ACTION_LOGIN, self.ACTION_LOGOUT, self.ACTION_DELETE)

    def to_dict(self) -> dict:
        """Sérialisation en dictionnaire."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity": self.entity,
            "entity_id": self.entity_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
