# application/use_cases/update_resource.py
"""Use case pour mettre à jour une ressource."""
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional
from domain.models.resource import ResourceType
from domain.repositories.interfaces import ResourceRepository
from domain.exceptions import ResourceNotFound


class UpdateResource:
    """Use case pour mettre à jour une ressource existante."""

    def __init__(self, resource_repo: ResourceRepository):
        self.resource_repo = resource_repo

    async def execute(self, resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mettre à jour une ressource.
        
        Args:
            resource_id: ID de la ressource à mettre à jour
            data: Dictionnaire avec les champs à mettre à jour
                  {
                    "name": str (optional),
                    "type": str (optional),
                    "description": str (optional),
                    "capacity": int (optional),
                    "location": str (optional),
                    "price": float (optional),
                    "is_active": bool (optional)
                  }
        
        Returns:
            Dictionnaire avec la ressource mise à jour
            
        Raises:
            ResourceNotFound: Si la ressource n'existe pas
        """
        resource_uuid = UUID(resource_id)
        resource = await self.resource_repo.get_by_id(resource_uuid)
        
        if not resource:
            raise ResourceNotFound(resource_id)
        
        # Mettre à jour les propriétés
        if "name" in data:
            resource.name = data["name"]
        
        if "type" in data:
            try:
                resource.type = ResourceType(data["type"])
            except ValueError:
                raise ValueError(
                    f"Type de ressource invalide. "
                    f"Types acceptés: {', '.join([t.value for t in ResourceType])}"
                )
        
        if "description" in data:
            resource.description = data["description"]
        
        if "capacity" in data:
            resource.capacity = data["capacity"]
        
        if "location" in data:
            resource.location = data["location"]
        
        if "price" in data:
            resource.price = data["price"]
        
        if "is_active" in data:
            resource.is_active = data["is_active"]
        
        resource.updated_at = datetime.now()
        
        # Enregistrer les modifications
        await self.resource_repo.save(resource)
        
        return self._format_resource(resource)

    async def deactivate(self, resource_id: str) -> Dict[str, Any]:
        """Désactiver une ressource."""
        resource_uuid = UUID(resource_id)
        resource = await self.resource_repo.get_by_id(resource_uuid)
        
        if not resource:
            raise ResourceNotFound(resource_id)
        
        resource.deactivate()
        await self.resource_repo.save(resource)
        
        return self._format_resource(resource)

    async def activate(self, resource_id: str) -> Dict[str, Any]:
        """Activer une ressource."""
        resource_uuid = UUID(resource_id)
        resource = await self.resource_repo.get_by_id(resource_uuid)
        
        if not resource:
            raise ResourceNotFound(resource_id)
        
        resource.activate()
        await self.resource_repo.save(resource)
        
        return self._format_resource(resource)

    def _format_resource(self, resource) -> Dict[str, Any]:
        """Formater une ressource pour la réponse API."""
        return {
            "id": str(resource.id),
            "name": resource.name,
            "type": resource.type.value,
            "description": resource.description,
            "capacity": resource.capacity,
            "location": resource.location,
            "price": resource.price,
            "is_active": resource.is_active,
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat(),
        }
