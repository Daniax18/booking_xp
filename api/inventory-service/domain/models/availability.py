from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AvailabilitySlot:
    """Represent one availability slot attached to a resource."""

    id: UUID
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    is_available: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    quantity_available: int = 1
    reason_if_unavailable: Optional[str] = None

    def __post_init__(self):
        """Validate domain invariants while allowing zero remaining quantity."""
        if self.end_time <= self.start_time:
            raise ValueError('La date de fin doit etre apres la date de debut')
        if self.quantity_available < 0:
            raise ValueError('La quantite disponible ne peut pas etre negative')

    def is_overlapping_with(self, other: 'AvailabilitySlot') -> bool:
        """Return whether this slot overlaps another slot."""
        return self.start_time < other.end_time and self.end_time > other.start_time

    def get_duration_minutes(self) -> int:
        """Return the slot duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def mark_unavailable(self, reason: str) -> None:
        """Mark the slot as unavailable with a business reason."""
        self.is_available = False
        self.reason_if_unavailable = reason
        self.updated_at = datetime.now()

    def mark_available(self) -> None:
        """Mark the slot as available again."""
        self.is_available = True
        self.reason_if_unavailable = None
        self.updated_at = datetime.now()
