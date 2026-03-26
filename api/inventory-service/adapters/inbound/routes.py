"""Routes HTTP de l'Inventory Service."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.schemas import (
    AvailabilitySlotResponse,
    CreateAvailabilitySlotRequest,
    CreateResourceRequest,
    CreateResourceResponse,
    ResourceResponse,
    UpdateAvailabilityRequest,
    UpdateResourceRequest,
)
from adapters.outbound.repositories import PostgresAvailabilityRepository, PostgresResourceRepository
from domain.exceptions import InvalidDateRange, ResourceNotFound
from domain.models.availability import AvailabilitySlot
from domain.models.resource import Resource
from domain.services import AvailabilityService, ResourceService
from infrastructure.database import get_session


router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


def _resource_type_to_str(resource_type) -> str:
    """Normaliser le type de ressource pour les reponses HTTP."""
    return getattr(resource_type, "value", str(resource_type))


def _to_resource_response(resource: Resource) -> ResourceResponse:
    """Convertir une entite Resource vers le schema de sortie HTTP."""
    return ResourceResponse(
        id=str(resource.id),
        name=resource.name,
        type=_resource_type_to_str(resource.type),
        description=resource.description,
        capacity=resource.capacity,
        location=resource.location,
        price=resource.price,
        is_active=resource.is_active,
        created_at=resource.created_at.isoformat(),
        updated_at=resource.updated_at.isoformat(),
    )


def _to_create_resource_response(resource: Resource) -> CreateResourceResponse:
    """Convertir une ressource creee vers son schema de reponse."""
    return CreateResourceResponse(
        id=str(resource.id),
        name=resource.name,
        type=_resource_type_to_str(resource.type),
        description=resource.description,
        capacity=resource.capacity,
        location=resource.location,
        price=resource.price,
        is_active=resource.is_active,
        created_at=resource.created_at.isoformat(),
    )


def _to_availability_response(slot: AvailabilitySlot) -> AvailabilitySlotResponse:
    """Convertir un creneau de disponibilite vers le schema HTTP."""
    return AvailabilitySlotResponse(
        id=str(slot.id),
        resource_id=str(slot.resource_id),
        start_time=slot.start_time.isoformat(),
        end_time=slot.end_time.isoformat(),
        is_available=slot.is_available,
        quantity_available=slot.quantity_available,
        reason_if_unavailable=slot.reason_if_unavailable,
        duration_minutes=int((slot.end_time - slot.start_time).total_seconds() / 60),
        created_at=slot.created_at.isoformat(),
        updated_at=slot.updated_at.isoformat(),
    )


def get_resource_service(session: AsyncSession = Depends(get_session)) -> ResourceService:
    """Construire le service metier des ressources pour la requete courante."""
    resource_repository = PostgresResourceRepository(session)
    return ResourceService(resource_repository)


def get_availability_service(session: AsyncSession = Depends(get_session)) -> AvailabilityService:
    """Construire le service metier des disponibilites pour la requete courante."""
    resource_repository = PostgresResourceRepository(session)
    availability_repository = PostgresAvailabilityRepository(session)
    return AvailabilityService(availability_repository, resource_repository)


@router.post("/resources", response_model=CreateResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: CreateResourceRequest,
    service: ResourceService = Depends(get_resource_service),
):
    """Creer une nouvelle ressource."""
    resource = await service.create_resource(
        name=request.name,
        resource_type=request.type.value,
        description=request.description,
        capacity=request.capacity,
        location=request.location,
        price=request.price,
    )
    return _to_create_resource_response(resource)


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    service: ResourceService = Depends(get_resource_service),
):
    """Recuperer une ressource par son identifiant."""
    try:
        resource = await service.get_resource_by_id(resource_id)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_resource_response(resource)


@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: str | None = Query(None, description="Filtrer par type de ressource"),
    service: ResourceService = Depends(get_resource_service),
):
    """Lister les ressources existantes."""
    resources = await service.list_resources(skip=skip, limit=limit, resource_type=type)
    return [_to_resource_response(resource) for resource in resources]


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    request: UpdateResourceRequest,
    service: ResourceService = Depends(get_resource_service),
):
    """Mettre a jour une ressource existante."""
    try:
        resource = await service.update_resource(
            resource_id=resource_id,
            name=request.name,
            resource_type=request.type.value if request.type else None,
            description=request.description,
            capacity=request.capacity,
            location=request.location,
            price=request.price,
            is_active=request.is_active,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_resource_response(resource)


@router.post("/resources/{resource_id}/deactivate", response_model=ResourceResponse)
async def deactivate_resource(
    resource_id: str,
    service: ResourceService = Depends(get_resource_service),
):
    """Desactiver une ressource."""
    try:
        resource = await service.deactivate_resource(resource_id)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_resource_response(resource)


@router.post("/resources/{resource_id}/activate", response_model=ResourceResponse)
async def activate_resource(
    resource_id: str,
    service: ResourceService = Depends(get_resource_service),
):
    """Activer une ressource."""
    try:
        resource = await service.activate_resource(resource_id)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_resource_response(resource)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    service: ResourceService = Depends(get_resource_service),
):
    """Supprimer une ressource."""
    try:
        await service.delete_resource(resource_id)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/availability", response_model=AvailabilitySlotResponse, status_code=status.HTTP_201_CREATED)
async def create_availability(
    request: CreateAvailabilitySlotRequest,
    service: AvailabilityService = Depends(get_availability_service),
):
    """Creer un creneau de disponibilite."""
    try:
        availability_slot = await service.create_availability(
            resource_id=request.resource_id,
            start_time=datetime.fromisoformat(request.start_time),
            end_time=datetime.fromisoformat(request.end_time),
            quantity=request.quantity,
            reason_if_unavailable=request.reason_if_unavailable,
        )
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvalidDateRange, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_availability_response(availability_slot)


@router.get("/availability/{resource_id}", response_model=List[AvailabilitySlotResponse])
async def get_availability(
    resource_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AvailabilityService = Depends(get_availability_service),
):
    """Lister les creneaux d'une ressource."""
    try:
        slots = await service.get_availability(resource_id=resource_id, skip=skip, limit=limit)
    except ResourceNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_to_availability_response(slot) for slot in slots]


@router.put("/availability/{slot_id}", response_model=AvailabilitySlotResponse)
async def update_availability(
    slot_id: str,
    request: UpdateAvailabilityRequest,
    service: AvailabilityService = Depends(get_availability_service),
):
    """Mettre a jour un creneau de disponibilite."""
    try:
        availability_slot = await service.update_availability(
            slot_id=slot_id,
            quantity=request.quantity,
            reason_if_unavailable=request.reason_if_unavailable,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "non trouve" in detail.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return _to_availability_response(availability_slot)


@router.delete("/availability/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability(
    slot_id: str,
    service: AvailabilityService = Depends(get_availability_service),
):
    """Supprimer un creneau de disponibilite."""
    try:
        await service.delete_availability(slot_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/health")
async def health_check():
    """Retourner un etat de sante simple pour le service inventory."""
    return {
        "service": "inventory-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
