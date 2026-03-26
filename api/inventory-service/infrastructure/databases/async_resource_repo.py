# infrastructure/databases/async_resource_repo.py
"""Implémentation async du repository pour les ressources."""
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.models.resource import Resource, ResourceType
from domain.repositories.interfaces import ResourceRepository
from domain.exceptions import ResourceNotFound, ResourceAlreadyExists
from infrastructure.databases.models import ResourceModel
from datetime import datetime


class ResourceRepositoryAsync(ResourceRepository):
    """Implémentation SQLAlchemy async du ResourceRepository."""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def save(self, resource: Resource) -> None:
        """Enregistrer une ressource (créer ou mettre à jour)."""
        stmt = select(ResourceModel).where(ResourceModel.id == str(resource.id))
        result = await self.session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            # Mise à jour
            existing.name = resource.name
            existing.type = resource.type.value
            existing.description = resource.description
            existing.capacity = resource.capacity
            existing.location = resource.location
            existing.price = resource.price
            existing.updated_at = datetime.utcnow()
        else:
            # Création
            new_resource = ResourceModel(
                id=str(resource.id),
                name=resource.name,
                type=resource.type.value,
                description=resource.description,
                capacity=resource.capacity,
                location=resource.location,
                price=resource.price,
                is_active=resource.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(new_resource)
        
        await self.session.flush()

    async def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """Récupérer une ressource par ID."""
        stmt = select(ResourceModel).where(ResourceModel.id == str(resource_id))
        result = await self.session.execute(stmt)
        resource_model = result.scalars().first()
        
        if not resource_model:
            return None
        
        return self._model_to_domain(resource_model)

    async def get_all(self) -> List[Resource]:
        """Récupérer toutes les ressources actives."""
        stmt = select(ResourceModel).where(ResourceModel.is_active == True)
        result = await self.session.execute(stmt)
        resources_models = result.scalars().all()
        
        return [self._model_to_domain(rm) for rm in resources_models]

    async def get_all_by_type(self, resource_type: str) -> List[Resource]:
        """Récupérer les ressources par type."""
        stmt = select(ResourceModel).where(
            (ResourceModel.type == resource_type) & (ResourceModel.is_active == True)
        )
        result = await self.session.execute(stmt)
        resources_models = result.scalars().all()
        
        return [self._model_to_domain(rm) for rm in resources_models]

    async def delete(self, resource_id: UUID) -> None:
        """Supprimer une ressource."""
        resource = await self.get_by_id(resource_id)
        if not resource:
            raise ResourceNotFound(resource_id)
        
        stmt = select(ResourceModel).where(ResourceModel.id == str(resource_id))
        result = await self.session.execute(stmt)
        resource_model = result.scalars().first()
        
        if resource_model:
            await self.session.delete(resource_model)
            await self.session.flush()

    async def exists(self, resource_id: UUID) -> bool:
        """Vérifier si une ressource existe."""
        stmt = select(ResourceModel).where(ResourceModel.id == str(resource_id))
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    @staticmethod
    def _model_to_domain(model: ResourceModel) -> Resource:
        """Convertir un modèle SQLAlchemy en entité de domaine."""
        return Resource(
            id=model.id,
            name=model.name,
            type=ResourceType(model.type),
            description=model.description,
            capacity=model.capacity,
            location=model.location,
            price=model.price,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
