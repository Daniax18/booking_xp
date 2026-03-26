# adapters/outbound/repositories.py
"""Implémentations concrètes des ports repository (adapters pour la persistence)."""
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.ports.repository import ResourceRepository, AvailabilityRepository
from adapters.outbound.orm_models import ResourceORM, AvailabilitySlotORM
from domain.models.resource import Resource
from domain.models.availability import AvailabilitySlot


class PostgresResourceRepository(ResourceRepository):
    """Repository PostgreSQL pour les ressources."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, resource: Resource) -> Resource:
        """Sauvegarder une ressource."""
        orm_resource = ResourceORM(
            id=resource.id or str(uuid4()),
            name=resource.name,
            type=resource.type,
            description=resource.description,
            capacity=resource.capacity,
            location=resource.location,
            price=resource.price,
            is_active=resource.is_active,
            created_at=resource.created_at or datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(orm_resource)
        await self.session.flush()
        resource.id = orm_resource.id
        return resource

    async def find_by_id(self, resource_id: str) -> Optional[Resource]:
        """Trouver une ressource par ID."""
        query = select(ResourceORM).where(ResourceORM.id == resource_id)
        result = await self.session.execute(query)
        orm_resource = result.scalars().first()
        return self._orm_to_domain(orm_resource) if orm_resource else None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Resource]:
        """Récupérer toutes les ressources."""
        query = select(ResourceORM).offset(skip).limit(limit)
        result = await self.session.execute(query)
        orm_resources = result.scalars().all()
        return [self._orm_to_domain(orm) for orm in orm_resources]

    async def update(self, resource: Resource) -> Resource:
        """Mettre à jour une ressource."""
        query = select(ResourceORM).where(ResourceORM.id == resource.id)
        result = await self.session.execute(query)
        orm_resource = result.scalars().first()
        
        if not orm_resource:
            raise ValueError(f"Ressource {resource.id} non trouvée")
        
        orm_resource.name = resource.name
        orm_resource.type = resource.type
        orm_resource.description = resource.description
        orm_resource.capacity = resource.capacity
        orm_resource.location = resource.location
        orm_resource.price = resource.price
        orm_resource.is_active = resource.is_active
        orm_resource.updated_at = datetime.utcnow()
        
        await self.session.flush()
        return self._orm_to_domain(orm_resource)

    async def delete(self, resource_id: str) -> None:
        """Supprimer une ressource."""
        query = select(ResourceORM).where(ResourceORM.id == resource_id)
        result = await self.session.execute(query)
        orm_resource = result.scalars().first()
        
        if orm_resource:
            await self.session.delete(orm_resource)
            await self.session.flush()

    async def count(self) -> int:
        """Compter le nombre de ressources."""
        query = select(ResourceORM)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    @staticmethod
    def _orm_to_domain(orm_resource: ResourceORM) -> Resource:
        """Convertir un ORM en domain model."""
        return Resource(
            id=orm_resource.id,
            name=orm_resource.name,
            type=orm_resource.type,
            description=orm_resource.description,
            capacity=orm_resource.capacity,
            location=orm_resource.location,
            price=orm_resource.price,
            is_active=orm_resource.is_active,
            created_at=orm_resource.created_at,
            updated_at=orm_resource.updated_at,
        )


class PostgresAvailabilityRepository(AvailabilityRepository):
    """Repository PostgreSQL pour les créneaux de disponibilité."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, availability_slot: AvailabilitySlot) -> AvailabilitySlot:
        """Sauvegarder un créneau de disponibilité."""
        orm_slot = AvailabilitySlotORM(
            id=availability_slot.id or str(uuid4()),
            resource_id=availability_slot.resource_id,
            start_time=availability_slot.start_time,
            end_time=availability_slot.end_time,
            is_available=availability_slot.is_available,
            quantity_available=availability_slot.quantity_available,
            reason_if_unavailable=availability_slot.reason_if_unavailable,
            created_at=availability_slot.created_at or datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(orm_slot)
        await self.session.flush()
        availability_slot.id = orm_slot.id
        return availability_slot

    async def find_by_id(self, slot_id: str) -> Optional[AvailabilitySlot]:
        """Trouver un créneau par ID."""
        query = select(AvailabilitySlotORM).where(AvailabilitySlotORM.id == slot_id)
        result = await self.session.execute(query)
        orm_slot = result.scalars().first()
        return self._orm_to_domain(orm_slot) if orm_slot else None

    async def find_by_resource_id(self, resource_id: str, skip: int = 0, limit: int = 100) -> List[AvailabilitySlot]:
        """Trouver les créneaux par ID de ressource."""
        query = select(AvailabilitySlotORM).where(
            AvailabilitySlotORM.resource_id == resource_id
        ).offset(skip).limit(limit)
        result = await self.session.execute(query)
        orm_slots = result.scalars().all()
        return [self._orm_to_domain(orm) for orm in orm_slots]

    async def update(self, availability_slot: AvailabilitySlot) -> AvailabilitySlot:
        """Mettre à jour un créneau de disponibilité."""
        query = select(AvailabilitySlotORM).where(AvailabilitySlotORM.id == availability_slot.id)
        result = await self.session.execute(query)
        orm_slot = result.scalars().first()
        
        if not orm_slot:
            raise ValueError(f"Créneau {availability_slot.id} non trouvé")
        
        orm_slot.is_available = availability_slot.is_available
        orm_slot.quantity_available = availability_slot.quantity_available
        orm_slot.reason_if_unavailable = availability_slot.reason_if_unavailable
        orm_slot.updated_at = datetime.utcnow()
        
        await self.session.flush()
        return self._orm_to_domain(orm_slot)

    async def delete(self, slot_id: str) -> None:
        """Supprimer un créneau."""
        query = select(AvailabilitySlotORM).where(AvailabilitySlotORM.id == slot_id)
        result = await self.session.execute(query)
        orm_slot = result.scalars().first()
        
        if orm_slot:
            await self.session.delete(orm_slot)
            await self.session.flush()

    @staticmethod
    def _orm_to_domain(orm_slot: AvailabilitySlotORM) -> AvailabilitySlot:
        """Convertir un ORM en domain model."""
        return AvailabilitySlot(
            id=orm_slot.id,
            resource_id=orm_slot.resource_id,
            start_time=orm_slot.start_time,
            end_time=orm_slot.end_time,
            is_available=orm_slot.is_available,
            quantity_available=orm_slot.quantity_available,
            reason_if_unavailable=orm_slot.reason_if_unavailable,
            created_at=orm_slot.created_at,
            updated_at=orm_slot.updated_at,
        )
