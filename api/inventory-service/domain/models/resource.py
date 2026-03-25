# domain/models/resource.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import Optional


class ResourceType(str, Enum):
    """Énumération des types de ressources disponibles."""
    ROOM = "room"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    SERVICE = "service"


@dataclass
class Resource:
    """
    Entité de domaine représentant une ressource (salle, équipement, véhicule, service).
    """
    id: UUID
    name: str
    type: ResourceType
    description: str
    capacity: int  # Nombre de personnes ou unités disponibles
    location: str
    price: float  # Prix par unité de temps
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        """Validations du domaine."""
        if self.capacity <= 0:
            raise ValueError("La capacité doit être positive")
        if self.price < 0:
            raise ValueError("Le prix ne peut pas être négatif")
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Le nom de la ressource est obligatoire")
    
    def deactivate(self) -> None:
        """Désactiver la ressource."""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Activer la ressource."""
        self.is_active = True
        self.updated_at = datetime.now()