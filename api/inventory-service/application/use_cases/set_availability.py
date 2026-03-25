# application/use_cases/set_availability.py
"""Use case pour définir la disponibilité d'une ressource."""
from uuid import uuid4, UUID
from datetime import datetime
from typing import Dict, Any, List
from domain.models.availability import AvailabilitySlot
from domain.repositories.interfaces import ResourceRepository, AvailabilityRepository
from domain.exceptions import (
    ResourceNotFound,
    AvailabilityOverlapError,
    InvalidDateRange
)


class SetAvailability:
    """Use case pour définir/configurer la disponibilité d'une ressource."""

    def __init__(
        self,
        resource_repo: ResourceRepository,
        availability_repo: AvailabilityRepository
    ):
        self.resource_repo = resource_repo
        self.availability_repo = availability_repo

    def execute(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        quantity: int = 1,
        reason_if_unavailable: str = None
    ) -> Dict[str, Any]:
        """
        Créer un créneau de disponibilité pour une ressource.
        
        Args:
            resource_id: ID de la ressource
            start_time: Début du créneau
            end_time: Fin du créneau
            quantity: Quantité disponible (par défaut 1)
            reason_if_unavailable: Raison si le créneau est indisponible
            
        Returns:
            Dictionnaire avec les données du créneau créé
            
        Raises:
            ResourceNotFound: Si la ressource n'existe pas
            InvalidDateRange: Si les dates sont invalides
        """
        resource_uuid = UUID(resource_id)
        
        # Vérifier que la ressource existe
        if not self.resource_repo.exists(resource_uuid):
            raise ResourceNotFound(resource_id)
        
        # Valider les dates
        if end_time <= start_time:
            raise InvalidDateRange(
                str(start_time),
                str(end_time)
            )
        
        # Vérifier les chevauchements
        existing_slots = self.availability_repo.get_by_resource_and_period(
            resource_uuid, start_time, end_time
        )
        
        new_slot = AvailabilitySlot(
            id=uuid4(),
            resource_id=resource_uuid,
            start_time=start_time,
            end_time=end_time,
            is_available=reason_if_unavailable is None,
            quantity_available=quantity,
            reason_if_unavailable=reason_if_unavailable
        )
        
        # Vérifier les chevauchements
        for existing_slot in existing_slots:
            if new_slot.is_overlapping_with(existing_slot):
                raise AvailabilityOverlapError(
                    str(new_slot.id),
                    str(existing_slot.id)
                )
        
        # Enregistrer le créneau
        self.availability_repo.save_slot(new_slot)
        
        return self._format_slot(new_slot)

    def mark_unavailable(
        self,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
        reason: str
    ) -> Dict[str, Any]:
        """
        Créer un créneau d'indisponibilité pour une ressource.
        (Utile pour les périodes de maintenance, fermetures, etc.)
        """
        return self.execute(
            resource_id,
            start_time,
            end_time,
            quantity=0,
            reason_if_unavailable=reason
        )

    def delete_availability_slot(self, slot_id: str) -> None:
        """Supprimer un créneau de disponibilité."""
        slot_uuid = UUID(slot_id)
        self.availability_repo.delete_slot(slot_uuid)

    def update_availability_slot(
        self,
        slot_id: str,
        is_available: bool = None,
        quantity: int = None,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Mettre à jour un créneau de disponibilité existant.
        
        Args:
            slot_id: ID du créneau
            is_available: Nouvelle disponibilité (optionnel)
            quantity: Nouvelle quantité (optionnel)
            reason: Nouvelle raison d'indisponibilité (optionnel)
        """
        slot_uuid = UUID(slot_id)
        slot = self.availability_repo.get_slot_by_id(slot_uuid)
        
        if not slot:
            raise ValueError(f"Créneau {slot_id} non trouvé")
        
        # Mettre à jour les propriétés
        if is_available is not None:
            slot.is_available = is_available
        
        if quantity is not None:
            slot.quantity_available = quantity
        
        if reason is not None:
            slot.reason_if_unavailable = reason
        
        slot.updated_at = datetime.now()
        
        # Enregistrer les modifications
        self.availability_repo.save_slot(slot)
        
        return self._format_slot(slot)

    def bulk_create_availability(
        self,
        resource_id: str,
        slots_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Créer plusieurs créneaux de disponibilité à la fois.
        
        Args:
            resource_id: ID de la ressource
            slots_data: Liste de dictionnaires avec les données des créneaux
                        [
                          {
                            "start_time": datetime,
                            "end_time": datetime,
                            "quantity": int (optional),
                            "reason_if_unavailable": str (optional)
                          },
                          ...
                        ]
        
        Returns:
            Liste des créneaux créés
        """
        created_slots = []
        
        for slot_data in slots_data:
            created_slot = self.execute(
                resource_id,
                slot_data["start_time"],
                slot_data["end_time"],
                slot_data.get("quantity", 1),
                slot_data.get("reason_if_unavailable")
            )
            created_slots.append(created_slot)
        
        return created_slots

    def _format_slot(self, slot: AvailabilitySlot) -> Dict[str, Any]:
        """Formater un créneau pour la réponse API."""
        return {
            "id": str(slot.id),
            "resource_id": str(slot.resource_id),
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "is_available": slot.is_available,
            "quantity_available": slot.quantity_available,
            "reason_if_unavailable": slot.reason_if_unavailable,
            "duration_minutes": slot.get_duration_minutes(),
            "created_at": slot.created_at.isoformat(),
            "updated_at": slot.updated_at.isoformat(),
        }
