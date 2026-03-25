# domain/services/availability_service.py
"""Service métier pour la gestion de la disponibilité des ressources."""
from datetime import datetime
from uuid import UUID
from typing import List
from domain.models.availability import AvailabilitySlot
from domain.repositories.interfaces import AvailabilityRepository
from domain.exceptions import (
    NoAvailabilityFound,
    InsufficientCapacity,
    AvailabilityOverlapError,
)


class AvailabilityService:
    """
    Service metier pour la gestion de la disponibilité.
    Encapsule la logique métier complexe de vérification de disponibilité.
    """

    def __init__(self, availability_repo: AvailabilityRepository):
        self.availability_repo = availability_repo

    def is_available(
        self, 
        resource_id: UUID, 
        start_time: datetime, 
        end_time: datetime,
        required_quantity: int = 1
    ) -> bool:
        """
        Vérifier si une ressource est disponible pour une période donnée.
        
        Args:
            resource_id: ID de la ressource
            start_time: Début de la période souhaitée
            end_time: Fin de la période souhaitée
            required_quantity: Quantité requise (par défaut 1)
            
        Returns:
            True si disponible, False sinon
        """
        slots = self.availability_repo.get_by_resource_and_period(
            resource_id, start_time, end_time
        )

        for slot in slots:
            if not slot.is_available:
                continue

            # Vérifier si le créneau couvre complètement la période demandée
            if slot.start_time <= start_time and slot.end_time >= end_time:
                if slot.quantity_available >= required_quantity:
                    return True

        return False

    def get_available_slots(
        self,
        resource_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[AvailabilitySlot]:
        """
        Récupérer les créneaux disponibles pour une période.
        
        Returns:
            Liste des créneaux disponibles
        """
        slots = self.availability_repo.get_by_resource_and_period(
            resource_id, start_time, end_time
        )
        return [slot for slot in slots if slot.is_available]

    def find_next_available_slot(
        self,
        resource_id: UUID,
        start_time: datetime,
        duration_minutes: int,
        required_quantity: int = 1
    ) -> AvailabilitySlot:
        """
        Trouver le prochain créneau disponible à partir d'une date donnée.
        
        Raises:
            NoAvailabilityFound: Si aucun créneau n'est disponible
        """
        from datetime import timedelta
        
        # Rechercher un créneau pour les 30 jours à venir
        end_search = start_time + timedelta(days=30)
        slots = self.availability_repo.get_by_resource_and_period(
            resource_id, start_time, end_search
        )
        
        available_slots = self.get_available_slots(
            resource_id, start_time, end_search
        )
        
        if not available_slots:
            raise NoAvailabilityFound(
                str(resource_id), 
                str(start_time), 
                str(end_search)
            )
        
        # Trouver le créneau qui peut accueillir la durée demandée
        for slot in available_slots:
            if (slot.get_duration_minutes() >= duration_minutes and 
                slot.quantity_available >= required_quantity):
                return slot
        
        raise NoAvailabilityFound(
            str(resource_id),
            str(start_time),
            str(end_search)
        )

    def check_overlap(self, slot1: AvailabilitySlot, slot2: AvailabilitySlot) -> bool:
        """
        Vérifier si deux créneaux se chevauchent.
        """
        return slot1.is_overlapping_with(slot2)

    def get_utilization_rate(
        self,
        resource_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """
        Calculer le taux d'utilisation d'une ressource sur une période.
        
        Returns:
            Taux entre 0 et 1 (0 = 0%, 1 = 100%)
        """
        all_slots = self.availability_repo.get_by_resource_and_period(
            resource_id, start_time, end_time
        )
        
        if not all_slots:
            return 0.0
        
        unavailable_minutes = sum(
            slot.get_duration_minutes() 
            for slot in all_slots 
            if not slot.is_available
        )
        
        total_minutes = sum(slot.get_duration_minutes() for slot in all_slots)
        
        if total_minutes == 0:
            return 0.0
        
        return unavailable_minutes / total_minutes