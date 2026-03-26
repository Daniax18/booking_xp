"""Use case pour la creation d'une ressource."""
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from domain.exceptions import DomainException
from domain.models.resource import Resource, ResourceType
from domain.repositories.interfaces import ResourceRepository


class CreateResource:
    """Use case pour creer une nouvelle ressource metier."""

    def __init__(self, resource_repo: ResourceRepository):
        """Store the repository used to persist created resources."""
        self.resource_repo = resource_repo

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and persist a resource using the Booking XP business types."""
        try:
            resource_type = ResourceType(data.get('type'))
        except ValueError as exc:
            raise ValueError(
                f"Type de ressource invalide. Types acceptes: {', '.join([t.value for t in ResourceType])}"
            ) from exc

        resource = Resource(
            id=uuid4(),
            name=data['name'],
            type=resource_type,
            description=data.get('description', ''),
            capacity=data['capacity'],
            location=data['location'],
            price=data['price'],
            created_at=datetime.now(),
        )

        await self.resource_repo.save(resource)

        return {
            'id': str(resource.id),
            'name': resource.name,
            'type': resource.type.value,
            'description': resource.description,
            'capacity': resource.capacity,
            'location': resource.location,
            'price': resource.price,
            'is_active': resource.is_active,
            'created_at': resource.created_at.isoformat(),
        }
