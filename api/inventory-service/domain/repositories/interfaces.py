# domain/repositories/interfaces.py
from abc import ABC, abstractmethod
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from domain.models.resource import Resource
from domain.models.availability import AvailabilitySlot


class ResourceRepository(ABC):
    """Interface du repository pour la gestion des ressources."""

    @abstractmethod
    async def save(self, resource: Resource) -> None:
        """Enregistrer une ressource (créer ou mettre à jour)."""
        pass

    @abstractmethod
    async def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """Récupérer une ressource par ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Resource]:
        """Récupérer toutes les ressources actives."""
        pass

    @abstractmethod
    async def get_all_by_type(self, resource_type: str) -> List[Resource]:
        """Récupérer les ressources par type."""
        pass

    @abstractmethod
    async def delete(self, resource_id: UUID) -> None:
        """Supprimer une ressource."""
        pass

    @abstractmethod
    async def exists(self, resource_id: UUID) -> bool:
        """Vérifier si une ressource existe."""
        pass


class AvailabilityRepository(ABC):
    """Interface du repository pour la gestion de la disponibilité."""

    @abstractmethod
    async def get_by_resource(self, resource_id: UUID) -> List[AvailabilitySlot]:
        """Récupérer tous les créneaux de disponibilité pour une ressource."""
        pass

    @abstractmethod
    async def get_by_resource_and_period(
        self, 
        resource_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[AvailabilitySlot]:
        """Récupérer les créneaux de disponibilité pour une période donnée."""
        pass

    @abstractmethod
    async def save_slot(self, slot: AvailabilitySlot) -> None:
        """Enregistrer un créneau de disponibilité."""
        pass

    @abstractmethod
    async def delete_slot(self, slot_id: UUID) -> None:
        """Supprimer un créneau de disponibilité."""
        pass

    @abstractmethod
    async def get_slot_by_id(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        """Récupérer un créneau par ID."""
        pass

    @abstractmethod
    async def get_slots_by_ids(self, slot_ids: List[UUID]) -> List[AvailabilitySlot]:
        """Récupérer plusieurs créneaux par leurs IDs."""
        pass