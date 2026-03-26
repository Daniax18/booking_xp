# domain/models/availability.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from typing import Optional


@dataclass
class AvailabilitySlot:
    """
    Entité de domaine représentant un créneau de disponibilité pour une ressource.
    """
    id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    is_available: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    quantity_available: int = 1  # Nombre d'unités disponibles pour ce créneau
    reason_if_unavailable: Optional[str] = None  # Raison de l'indisponibilité si applicable
    
    def __post_init__(self):
        """Validations du domaine."""
        if self.end_time <= self.start_time:
            raise ValueError("La date de fin doit être après la date de début")
        if self.quantity_available <= 0:
            raise ValueError("La quantité disponible doit être positive")
    
    def is_overlapping_with(self, other: 'AvailabilitySlot') -> bool:
        """Vérifie si ce créneau chevauche un autre."""
        return self.start_time < other.end_time and self.end_time > other.start_time
    
    def get_duration_minutes(self) -> int:
        """Retourne la durée du créneau en minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def mark_unavailable(self, reason: str) -> None:
        """Marquer le créneau comme indisponible."""
        self.is_available = False
        self.reason_if_unavailable = reason
        self.updated_at = datetime.now()
    
    def mark_available(self) -> None:
        """Marquer le créneau comme disponible."""
        self.is_available = True
        self.reason_if_unavailable = None
        self.updated_at = datetime.now()