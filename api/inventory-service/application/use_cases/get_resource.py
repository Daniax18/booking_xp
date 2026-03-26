# application/use_cases/get_resource.py
"""Use case pour récupérer les informations d'une ressource."""
from uuid import UUID
from typing import Dict, Any, List
from domain.repositories.interfaces import ResourceRepository
from domain.exceptions import ResourceNotFound


class GetResource:
    """Use case pour récupérer les informations d'une ressource."""

    def __init__(self, resource_repo: ResourceRepository):
        self.resource_repo = resource_repo

    async def execute(self, resource_id: str) -> Dict[str, Any]:
        """
        Récupérer les détails d'une ressource.
        
        Raises:
            ResourceNotFound: Si la ressource n'existe pas
        """
        resource_uuid = UUID(resource_id)
        resource = await self.resource_repo.get_by_id(resource_uuid)
        
        if not resource:
            raise ResourceNotFound(resource_id)
        
        return self._format_resource(resource)

    async def get_all_resources(self) -> List[Dict[str, Any]]:
        """Récupérer toutes les ressources actives."""
        resources = await self.resource_repo.get_all()
        return [self._format_resource(r) for r in resources]

    async def get_resources_by_type(self, resource_type: str) -> List[Dict[str, Any]]:
        """Récupérer tous les ressources d'un type spécifique."""
        resources = await self.resource_repo.get_all_by_type(resource_type)
        return [self._format_resource(r) for r in resources]

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
