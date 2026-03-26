"""Service de domaine pour la gestion des ressources."""

from datetime import datetime
from uuid import uuid4

from domain.exceptions import ResourceNotFound
from domain.models.resource import Resource
from domain.ports.repository import ResourceRepository


class ResourceService:
    """Encapsuler les regles metier appliquees aux ressources."""

    def __init__(self, resource_repository: ResourceRepository):
        """Initialiser le service avec son port de persistence."""
        self._resource_repository = resource_repository

    async def create_resource(
        self,
        *,
        name: str,
        resource_type: str,
        description: str,
        capacity: int,
        location: str,
        price: float,
    ) -> Resource:
        """Creer puis persister une nouvelle ressource."""
        resource = Resource(
            id=str(uuid4()),
            name=name,
            type=resource_type,
            description=description,
            capacity=capacity,
            location=location,
            price=price,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return await self._resource_repository.save(resource)

    async def get_resource_by_id(self, resource_id: str) -> Resource:
        """Recuperer une ressource existante ou lever une erreur explicite."""
        resource = await self._resource_repository.find_by_id(resource_id)
        if not resource:
            raise ResourceNotFound(resource_id)
        return resource

    async def list_resources(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        resource_type: str | None = None,
    ) -> list[Resource]:
        """Lister les ressources disponibles."""
        resources = await self._resource_repository.find_all(skip=skip, limit=limit)
        if resource_type is None:
            return resources
        return [
            resource
            for resource in resources
            if getattr(resource.type, "value", resource.type) == resource_type
        ]

    async def update_resource(
        self,
        *,
        resource_id: str,
        name: str | None = None,
        resource_type: str | None = None,
        description: str | None = None,
        capacity: int | None = None,
        location: str | None = None,
        price: float | None = None,
        is_active: bool | None = None,
    ) -> Resource:
        """Mettre a jour les champs modifiables d'une ressource."""
        resource = await self.get_resource_by_id(resource_id)

        if name is not None:
            resource.name = name
        if resource_type is not None:
            resource.type = resource_type
        if description is not None:
            resource.description = description
        if capacity is not None:
            resource.capacity = capacity
        if location is not None:
            resource.location = location
        if price is not None:
            resource.price = price
        if is_active is not None:
            resource.is_active = is_active

        resource.updated_at = datetime.utcnow()
        return await self._resource_repository.update(resource)

    async def activate_resource(self, resource_id: str) -> Resource:
        """Activer une ressource existante."""
        return await self.update_resource(resource_id=resource_id, is_active=True)

    async def deactivate_resource(self, resource_id: str) -> Resource:
        """Desactiver une ressource existante."""
        return await self.update_resource(resource_id=resource_id, is_active=False)

    async def delete_resource(self, resource_id: str) -> None:
        """Supprimer definitivement une ressource existante."""
        await self.get_resource_by_id(resource_id)
        await self._resource_repository.delete(resource_id)
