# infrastructure/databases/availability_repo.py
"""Implémentation du repository pour la disponibilité."""
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from domain.models.availability import AvailabilitySlot
from domain.repositories.interfaces import AvailabilityRepository
from domain.exceptions import NoAvailabilityFound
from infrastructure.databases.models import AvailabilitySlotModel


class AvailabilityRepositorySQLAlchemy(AvailabilityRepository):
    """Implémentation SQLAlchemy du AvailabilityRepository."""

    def __init__(self, db_session: Session):
        self.session = db_session

    def get_by_resource(self, resource_id: UUID) -> List[AvailabilitySlot]:
        """Récupérer tous les créneaux de disponibilité pour une ressource."""
        slot_models = self.session.query(AvailabilitySlotModel).filter_by(
            resource_id=str(resource_id)
        ).order_by(AvailabilitySlotModel.start_time).all()

        return [self._map_model_to_domain(model) for model in slot_models]

    def get_by_resource_and_period(
        self,
        resource_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[AvailabilitySlot]:
        """Récupérer les créneaux de disponibilité pour une période donnée."""
        slot_models = self.session.query(AvailabilitySlotModel).filter(
            AvailabilitySlotModel.resource_id == str(resource_id),
            AvailabilitySlotModel.start_time >= start_time,
            AvailabilitySlotModel.end_time <= end_time
        ).order_by(AvailabilitySlotModel.start_time).all()

        return [self._map_model_to_domain(model) for model in slot_models]

    def save_slot(self, slot: AvailabilitySlot) -> None:
        """Enregistrer un créneau de disponibilité."""
        existing = self.session.query(AvailabilitySlotModel).filter_by(
            id=str(slot.id)
        ).first()

        if existing:
            # Mise à jour
            existing.resource_id = str(slot.resource_id)
            existing.start_time = slot.start_time
            existing.end_time = slot.end_time
            existing.is_available = slot.is_available
            existing.quantity_available = slot.quantity_available
            existing.reason_if_unavailable = slot.reason_if_unavailable
            existing.updated_at = datetime.utcnow()
        else:
            # Création
            slot_model = AvailabilitySlotModel(
                id=str(slot.id),
                resource_id=str(slot.resource_id),
                start_time=slot.start_time,
                end_time=slot.end_time,
                is_available=slot.is_available,
                quantity_available=slot.quantity_available,
                reason_if_unavailable=slot.reason_if_unavailable,
                created_at=slot.created_at,
                updated_at=datetime.utcnow()
            )
            self.session.add(slot_model)

        self.session.commit()

    def delete_slot(self, slot_id: UUID) -> None:
        """Supprimer un créneau de disponibilité."""
        slot_model = self.session.query(AvailabilitySlotModel).filter_by(
            id=str(slot_id)
        ).first()

        if not slot_model:
            raise NoAvailabilityFound(
                str(slot_id), "", ""
            )

        self.session.delete(slot_model)
        self.session.commit()

    def get_slot_by_id(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        """Récupérer un créneau par ID."""
        slot_model = self.session.query(AvailabilitySlotModel).filter_by(
            id=str(slot_id)
        ).first()

        if not slot_model:
            return None

        return self._map_model_to_domain(slot_model)

    def get_slots_by_ids(self, slot_ids: List[UUID]) -> List[AvailabilitySlot]:
        """Récupérer plusieurs créneaux par leurs IDs."""
        slot_models = self.session.query(AvailabilitySlotModel).filter(
            AvailabilitySlotModel.id.in_([str(sid) for sid in slot_ids])
        ).all()

        return [self._map_model_to_domain(model) for model in slot_models]

    def _map_model_to_domain(self, model: AvailabilitySlotModel) -> AvailabilitySlot:
        """Mapper une instance SQLAlchemy vers le modèle de domaine."""
        return AvailabilitySlot(
            id=UUID(model.id),
            resource_id=UUID(model.resource_id),
            start_time=model.start_time,
            end_time=model.end_time,
            is_available=model.is_available,
            created_at=model.created_at,
            updated_at=model.updated_at,
            quantity_available=model.quantity_available,
            reason_if_unavailable=model.reason_if_unavailable
        )
