# domain/ports/repository.py
"""Contrats (interfaces) pour les adapters de persistence."""
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.models.resource import Resource
from domain.models.availability import AvailabilitySlot


class ResourceRepository(ABC):
    """Port (interface) pour la persistence des ressources."""

    @abstractmethod
    async def save(self, resource: Resource) -> Resource:
        """Sauvegarder une ressource."""
        pass

    @abstractmethod
    async def find_by_id(self, resource_id: str) -> Optional[Resource]:
        """Trouver une ressource par ID."""
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Resource]:
        """Récupérer toutes les ressources."""
        pass

    @abstractmethod
    async def update(self, resource: Resource) -> Resource:
        """Mettre à jour une ressource."""
        pass

    @abstractmethod
    async def delete(self, resource_id: str) -> None:
        """Supprimer une ressource."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Compter le nombre de ressources."""
        pass


class AvailabilityRepository(ABC):
    """Port (interface) pour la persistence des créneaux de disponibilité."""

    @abstractmethod
    async def save(self, availability_slot: AvailabilitySlot) -> AvailabilitySlot:
        """Sauvegarder un créneau de disponibilité."""
        pass

    @abstractmethod
    async def find_by_id(self, slot_id: str) -> Optional[AvailabilitySlot]:
        """Trouver un créneau par ID."""
        pass

    @abstractmethod
    async def find_by_resource_id(self, resource_id: str, skip: int = 0, limit: int = 100) -> List[AvailabilitySlot]:
        """Trouver les créneaux par ID de ressource."""
        pass

    @abstractmethod
    async def update(self, availability_slot: AvailabilitySlot) -> AvailabilitySlot:
        """Mettre à jour un créneau de disponibilité."""
        pass

    @abstractmethod
    async def delete(self, slot_id: str) -> None:
        """Supprimer un créneau."""
        pass
