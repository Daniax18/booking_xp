# infrastructure/databases/resource_repo.py
"""Implémentation du repository pour les ressources."""
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from domain.models.resource import Resource, ResourceType
from domain.repositories.interfaces import ResourceRepository
from domain.exceptions import ResourceNotFound, ResourceAlreadyExists
from infrastructure.databases.models import ResourceModel
from datetime import datetime


class ResourceRepositorySQLAlchemy(ResourceRepository):
    """Implémentation SQLAlchemy du ResourceRepository."""

    def __init__(self, db_session: Session):
        self.session = db_session

    def save(self, resource: Resource) -> None:
        """Enregistrer une ressource (créer ou mettre à jour)."""
        existing = self.session.query(ResourceModel).filter_by(
            id=str(resource.id)
        ).first()

        if existing:
            # Mise à jour
            existing.name = resource.name
            existing.type = resource.type.value
            existing.description = resource.description
            existing.capacity = resource.capacity
            existing.location = resource.location
            existing.price = resource.price
            existing.is_active = resource.is_active
            existing.updated_at = datetime.utcnow()
        else:
            # Création
            resource_model = ResourceModel(
                id=str(resource.id),
                name=resource.name,
                type=resource.type.value,
                description=resource.description,
                capacity=resource.capacity,
                location=resource.location,
                price=resource.price,
                is_active=resource.is_active,
                created_at=resource.created_at,
                updated_at=datetime.utcnow()
            )
            self.session.add(resource_model)

        self.session.commit()

    def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """Récupérer une ressource par ID."""
        resource_model = self.session.query(ResourceModel).filter_by(
            id=str(resource_id)
        ).first()

        if not resource_model:
            return None

        return self._map_model_to_domain(resource_model)

    def get_all(self) -> List[Resource]:
        """Récupérer toutes les ressources actives."""
        resource_models = self.session.query(ResourceModel).filter_by(
            is_active=True
        ).all()

        return [self._map_model_to_domain(model) for model in resource_models]

    def get_all_by_type(self, resource_type: str) -> List[Resource]:
        """Récupérer les ressources par type."""
        resource_models = self.session.query(ResourceModel).filter_by(
            type=resource_type,
            is_active=True
        ).all()

        return [self._map_model_to_domain(model) for model in resource_models]

    def delete(self, resource_id: UUID) -> None:
        """Supprimer une ressource."""
        resource_model = self.session.query(ResourceModel).filter_by(
            id=str(resource_id)
        ).first()

        if not resource_model:
            raise ResourceNotFound(str(resource_id))

        self.session.delete(resource_model)
        self.session.commit()

    def exists(self, resource_id: UUID) -> bool:
        """Vérifier si une ressource existe."""
        resource_model = self.session.query(ResourceModel).filter_by(
            id=str(resource_id)
        ).first()

        return resource_model is not None

    def _map_model_to_domain(self, model: ResourceModel) -> Resource:
        """Mapper une instance SQLAlchemy vers le modèle de domaine."""
        return Resource(
            id=UUID(model.id),
            name=model.name,
            type=ResourceType(model.type),
            description=model.description,
            capacity=model.capacity,
            location=model.location,
            price=model.price,
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active
        )
