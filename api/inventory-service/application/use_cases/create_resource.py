# application/use_cases/create_resource.py
"""Use case pour la création d'une ressource."""
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any
from domain.models.resource import Resource, ResourceType
from domain.repositories.interfaces import ResourceRepository
from domain.exceptions import DomainException


class CreateResource:
    """Use case pour créer une nouvelle ressource."""

    def __init__(self, resource_repo: ResourceRepository):
        self.resource_repo = resource_repo

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Créer une nouvelle ressource.
        
        Args:
            data: Dictionnaire contenant les données de la ressource
                  {
                    "name": str,
                    "type": str (room|equipment|vehicle|service),
                    "description": str,
                    "capacity": int,
                    "location": str,
                    "price": float
                  }
        
        Returns:
            Dictionnaire avec les données de la ressource créée
            
        Raises:
            DomainException: Si les données sont invalides
        """
        try:
            # Valider et convertir le type
            resource_type = ResourceType(data.get("type"))
        except ValueError:
            raise ValueError(
                f"Type de ressource invalide. "
                f"Types acceptés: {', '.join([t.value for t in ResourceType])}"
            )

        # Créer l'instance du domaine
        resource = Resource(
            id=uuid4(),
            name=data["name"],
            type=resource_type,
            description=data.get("description", ""),
            capacity=data["capacity"],
            location=data["location"],
            price=data["price"],
            created_at=datetime.now(),
        )

        # Enregistrer dans le repository
        self.resource_repo.save(resource)

        # Retourner la ressource créée
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
        }