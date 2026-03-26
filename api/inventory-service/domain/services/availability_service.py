"""Service de domaine pour la gestion des disponibilites."""

from datetime import datetime
from uuid import uuid4

from domain.exceptions import InvalidDateRange, ResourceNotFound
from domain.models.availability import AvailabilitySlot
from domain.ports.repository import AvailabilityRepository, ResourceRepository


class AvailabilityService:
    """Encapsuler les regles metier des creneaux de disponibilite."""

    def __init__(
        self,
        availability_repository: AvailabilityRepository,
        resource_repository: ResourceRepository,
    ):
        """Initialiser le service avec ses ports de persistence."""
        self._availability_repository = availability_repository
        self._resource_repository = resource_repository

    async def create_availability(
        self,
        *,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        quantity: int,
        reason_if_unavailable: str | None = None,
    ) -> AvailabilitySlot:
        """Creer un nouveau creneau de disponibilite pour une ressource."""
        resource = await self._resource_repository.find_by_id(resource_id)
        if not resource:
            raise ResourceNotFound(resource_id)

        if end_time <= start_time:
            raise InvalidDateRange(start_time.isoformat(), end_time.isoformat())

        availability_slot = AvailabilitySlot(
            id=str(uuid4()),
            resource_id=resource_id,
            start_time=start_time,
            end_time=end_time,
            is_available=reason_if_unavailable is None,
            quantity_available=quantity,
            reason_if_unavailable=reason_if_unavailable,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return await self._availability_repository.save(availability_slot)

    async def get_availability(
        self,
        *,
        resource_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AvailabilitySlot]:
        """Lister les creneaux d'une ressource existante."""
        resource = await self._resource_repository.find_by_id(resource_id)
        if not resource:
            raise ResourceNotFound(resource_id)
        return await self._availability_repository.find_by_resource_id(
            resource_id,
            skip=skip,
            limit=limit,
        )

    async def update_availability(
        self,
        *,
        slot_id: str,
        quantity: int | None = None,
        reason_if_unavailable: str | None = None,
    ) -> AvailabilitySlot:
        """Mettre a jour l'etat et la quantite d'un creneau."""
        availability_slot = await self._availability_repository.find_by_id(slot_id)
        if not availability_slot:
            raise ValueError(f"Creneau {slot_id} non trouve")

        if quantity is not None:
            availability_slot.quantity_available = quantity
        availability_slot.reason_if_unavailable = reason_if_unavailable
        availability_slot.is_available = reason_if_unavailable is None
        availability_slot.updated_at = datetime.utcnow()
        return await self._availability_repository.update(availability_slot)

    async def delete_availability(self, slot_id: str) -> None:
        """Supprimer un creneau existant."""
        availability_slot = await self._availability_repository.find_by_id(slot_id)
        if not availability_slot:
            raise ValueError(f"Creneau {slot_id} non trouve")
        await self._availability_repository.delete(slot_id)
