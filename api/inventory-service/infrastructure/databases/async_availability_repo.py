# infrastructure/databases/async_availability_repo.py
"""Implémentation async du repository pour la disponibilité."""
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from domain.models.availability import AvailabilitySlot
from domain.repositories.interfaces import AvailabilityRepository
from infrastructure.databases.models import AvailabilitySlotModel
from datetime import datetime


class AvailabilityRepositoryAsync(AvailabilityRepository):
    """Implémentation SQLAlchemy async du AvailabilityRepository."""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def get_by_resource(self, resource_id: UUID) -> List[AvailabilitySlot]:
        """Récupérer tous les créneaux de disponibilité pour une ressource."""
        stmt = select(AvailabilitySlotModel).where(
            AvailabilitySlotModel.resource_id == str(resource_id)
        )
        result = await self.session.execute(stmt)
        slots_models = result.scalars().all()
        
        return [self._model_to_domain(sm) for sm in slots_models]

    async def get_by_resource_and_period(
        self,
        resource_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[AvailabilitySlot]:
        """Récupérer les créneaux de disponibilité pour une période donnée."""
        stmt = select(AvailabilitySlotModel).where(
            and_(
                AvailabilitySlotModel.resource_id == str(resource_id),
                AvailabilitySlotModel.start_time >= start_time,
                AvailabilitySlotModel.end_time <= end_time
            )
        )
        result = await self.session.execute(stmt)
        slots_models = result.scalars().all()
        
        return [self._model_to_domain(sm) for sm in slots_models]

    async def save_slot(self, slot: AvailabilitySlot) -> None:
        """Enregistrer un créneau de disponibilité."""
        stmt = select(AvailabilitySlotModel).where(
            AvailabilitySlotModel.id == str(slot.id)
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            # Mise à jour
            existing.is_available = slot.is_available
            existing.quantity_available = slot.quantity_available
            existing.reason_if_unavailable = slot.reason_if_unavailable
            existing.updated_at = datetime.utcnow()
        else:
            # Création
            new_slot = AvailabilitySlotModel(
                id=str(slot.id),
                resource_id=str(slot.resource_id),
                start_time=slot.start_time,
                end_time=slot.end_time,
                is_available=slot.is_available,
                quantity_available=slot.quantity_available,
                reason_if_unavailable=slot.reason_if_unavailable,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(new_slot)
        
        await self.session.flush()

    async def delete_slot(self, slot_id: UUID) -> None:
        """Supprimer un créneau de disponibilité."""
        stmt = select(AvailabilitySlotModel).where(
            AvailabilitySlotModel.id == str(slot_id)
        )
        result = await self.session.execute(stmt)
        slot_model = result.scalars().first()
        
        if slot_model:
            await self.session.delete(slot_model)
            await self.session.flush()

    async def get_slot_by_id(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        """Récupérer un créneau par ID."""
        stmt = select(AvailabilitySlotModel).where(
            AvailabilitySlotModel.id == str(slot_id)
        )
        result = await self.session.execute(stmt)
        slot_model = result.scalars().first()
        
        if not slot_model:
            return None
        
        return self._model_to_domain(slot_model)

    async def get_slots_by_ids(self, slot_ids: List[UUID]) -> List[AvailabilitySlot]:
        """Récupérer plusieurs créneaux par leurs IDs."""
        slot_ids_str = [str(sid) for sid in slot_ids]
        stmt = select(AvailabilitySlotModel).where(
            AvailabilitySlotModel.id.in_(slot_ids_str)
        )
        result = await self.session.execute(stmt)
        slots_models = result.scalars().all()
        
        return [self._model_to_domain(sm) for sm in slots_models]

    @staticmethod
    def _model_to_domain(model: AvailabilitySlotModel) -> AvailabilitySlot:
        """Convertir un modèle SQLAlchemy en entité de domaine."""
        return AvailabilitySlot(
            id=model.id,
            resource_id=model.resource_id,
            start_time=model.start_time,
            end_time=model.end_time,
            is_available=model.is_available,
            quantity_available=model.quantity_available,
            reason_if_unavailable=model.reason_if_unavailable,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
