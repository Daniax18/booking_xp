from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class ResourceType(str, Enum):
    """Enumerate the business resource types supported by Booking XP."""

    HOTEL_ROOM = 'HOTEL_ROOM'
    RESTAURANT_TABLE = 'RESTAURANT_TABLE'
    VENUE = 'VENUE'


@dataclass
class Resource:
    """Represent a reservable business resource stored by inventory-service."""

    id: UUID
    name: str
    type: ResourceType
    description: str
    capacity: int
    location: str
    price: float
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def __post_init__(self):
        """Validate core business invariants when a resource is created or rebuilt."""
        if isinstance(self.type, str):
            self.type = ResourceType(self.type)
        if self.capacity <= 0:
            raise ValueError('La capacite doit etre positive')
        if self.price < 0:
            raise ValueError('Le prix ne peut pas etre negatif')
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError('Le nom de la ressource est obligatoire')

    def deactivate(self) -> None:
        """Deactivate the resource so it can no longer be reserved."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Reactivate the resource so it becomes reservable again."""
        self.is_active = True
        self.updated_at = datetime.now()
