# application/use_cases/get_availability.py
"""Use case pour récupérer la disponibilité d'une ressource."""
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List
from domain.repositories.interfaces import ResourceRepository, AvailabilityRepository
from domain.services.availability_service import AvailabilityService
from domain.exceptions import ResourceNotFound, NoAvailabilityFound


class GetAvailability:
    """Use case pour récupérer la disponibilité d'une ressource."""

    def __init__(
        self,
        resource_repo: ResourceRepository,
        availability_repo: AvailabilityRepository
    ):
        self.resource_repo = resource_repo
        self.availability_repo = availability_repo
        self.availability_service = AvailabilityService(availability_repo)

    def execute(self, resource_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Récupérer la disponibilité d'une ressource pour une période.
        
        Args:
            resource_id: ID de la ressource
            start_time: Début de la période
            end_time: Fin de la période
            
        Returns:
            Dictionnaire avec les disponibilités
            
        Raises:
            ResourceNotFound: Si la ressource n'existe pas
        """
        resource_uuid = UUID(resource_id)
        
        # Vérifier que la ressource existe
        if not self.resource_repo.exists(resource_uuid):
            raise ResourceNotFound(resource_id)
        
        # Récupérer les créneaux disponibles
        available_slots = self.availability_service.get_available_slots(
            resource_uuid, start_time, end_time
        )
        
        # Formatter les résultats
        slots_data = [
            {
                "id": str(slot.id),
                "resource_id": str(slot.resource_id),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "is_available": slot.is_available,
                "quantity_available": slot.quantity_available,
                "duration_minutes": slot.get_duration_minutes(),
            }
            for slot in available_slots
        ]
        
        return {
            "resource_id": resource_id,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            "available_slots": slots_data,
            "total_available_slots": len(available_slots),
            "total_available_minutes": sum(s.get_duration_minutes() for s in available_slots),
        }

    def check_availability(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Vérifier si une ressource est disponible pour une période donnée.
        
        Returns:
            Dictionnaire indiquant la disponibilité
        """
        resource_uuid = UUID(resource_id)
        
        # Vérifier que la ressource existe
        if not self.resource_repo.exists(resource_uuid):
            raise ResourceNotFound(resource_id)
        
        is_available = self.availability_service.is_available(
            resource_uuid, start_time, end_time, quantity
        )
        
        return {
            "resource_id": resource_id,
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            "is_available": is_available,
            "quantity_required": quantity,
        }

    def get_next_available_slot(
        self,
        resource_id: str,
        start_time: datetime,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Trouver le prochain créneau disponible.
        
        Raises:
            NoAvailabilityFound: Si aucun créneau n'est disponible
        """
        resource_uuid = UUID(resource_id)
        
        # Vérifier que la ressource existe
        if not self.resource_repo.exists(resource_uuid):
            raise ResourceNotFound(resource_id)
        
        slot = self.availability_service.find_next_available_slot(
            resource_uuid, start_time, duration_minutes
        )
        
        return {
            "resource_id": resource_id,
            "requested_start": start_time.isoformat(),
            "requested_duration_minutes": duration_minutes,
            "available_slot": {
                "id": str(slot.id),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "quantity_available": slot.quantity_available,
                "duration_minutes": slot.get_duration_minutes(),
            }
        }
