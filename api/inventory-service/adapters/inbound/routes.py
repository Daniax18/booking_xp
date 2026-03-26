# adapters/inbound/routes.py
"""Endpoints FastAPI (adapters inbound) pour l'API REST."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
from uuid import uuid4

from infrastructure.database import get_session
from adapters.inbound.schemas import (
    CreateResourceRequest, CreateResourceResponse, ResourceResponse,
    UpdateResourceRequest, CreateAvailabilitySlotRequest, AvailabilitySlotResponse,
    GetAvailabilityRequest, AvailabilityCheckResponse, ErrorResponse
)
from adapters.outbound.repositories import PostgresResourceRepository, PostgresAvailabilityRepository
from domain.models.resource import Resource
from domain.models.availability import AvailabilitySlot
from domain.exceptions import ResourceNotFound, ResourceInactive, InvalidDateRange, DomainException

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


# ====== Dependency Injection ======

async def get_resource_repository(session: AsyncSession = Depends(get_session)) -> PostgresResourceRepository:
    """Provider pour le repository des ressources."""
    return PostgresResourceRepository(session)


async def get_availability_repository(session: AsyncSession = Depends(get_session)) -> PostgresAvailabilityRepository:
    """Provider pour le repository des créneaux de disponibilité."""
    return PostgresAvailabilityRepository(session)


# ====== Resource Endpoints ======

@router.post("/resources", response_model=CreateResourceResponse, status_code=201)
async def create_resource(
    request: CreateResourceRequest,
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository)
):
    """Créer une nouvelle ressource."""
    try:
        resource = Resource(
            id=str(uuid4()),
            name=request.name,
            type=request.type.value,
            description=request.description,
            capacity=request.capacity,
            location=request.location,
            price=request.price,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        saved_resource = await resource_repo.save(resource)
        
        return CreateResourceResponse(
            id=saved_resource.id,
            name=saved_resource.name,
            type=saved_resource.type,
            description=saved_resource.description,
            capacity=saved_resource.capacity,
            location=saved_resource.location,
            price=saved_resource.price,
            is_active=saved_resource.is_active,
            created_at=saved_resource.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository)
):
    """Récupérer une ressource par ID."""
    resource = await resource_repo.find_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")
    
    return ResourceResponse(
        id=resource.id,
        name=resource.name,
        type=resource.type,
        description=resource.description,
        capacity=resource.capacity,
        location=resource.location,
        price=resource.price,
        is_active=resource.is_active,
        created_at=resource.created_at.isoformat(),
        updated_at=resource.updated_at.isoformat()
    )


@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository)
):
    """Récupérer la liste des ressources."""
    resources = await resource_repo.find_all(skip=skip, limit=limit)
    return [
        ResourceResponse(
            id=r.id,
            name=r.name,
            type=r.type,
            description=r.description,
            capacity=r.capacity,
            location=r.location,
            price=r.price,
            is_active=r.is_active,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat()
        )
        for r in resources
    ]


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    request: UpdateResourceRequest,
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository),
    db: AsyncSession = Depends(get_session)
):
    """Mettre à jour une ressource."""
    try:
        resource = await resource_repo.find_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Ressource non trouvée")
        
        # Mettre à jour les champs fournis
        if request.name is not None:
            resource.name = request.name
        if request.type is not None:
            resource.type = request.type.value
        if request.description is not None:
            resource.description = request.description
        if request.capacity is not None:
            resource.capacity = request.capacity
        if request.location is not None:
            resource.location = request.location
        if request.price is not None:
            resource.price = request.price
        if request.is_active is not None:
            resource.is_active = request.is_active
        
        resource.updated_at = datetime.utcnow()
        updated_resource = await resource_repo.update(resource)
        await db.commit()
        
        return ResourceResponse(
            id=updated_resource.id,
            name=updated_resource.name,
            type=updated_resource.type,
            description=updated_resource.description,
            capacity=updated_resource.capacity,
            location=updated_resource.location,
            price=updated_resource.price,
            is_active=updated_resource.is_active,
            created_at=updated_resource.created_at.isoformat(),
            updated_at=updated_resource.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/resources/{resource_id}", status_code=204)
async def delete_resource(
    resource_id: str,
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository),
    db: AsyncSession = Depends(get_session)
):
    """Supprimer une ressource."""
    resource = await resource_repo.find_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")
    
    await resource_repo.delete(resource_id)
    await db.commit()


# ====== Availability Endpoints ======

@router.post("/availability", response_model=AvailabilitySlotResponse, status_code=201)
async def create_availability(
    request: CreateAvailabilitySlotRequest,
    availability_repo: PostgresAvailabilityRepository = Depends(get_availability_repository),
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository),
    db: AsyncSession = Depends(get_session)
):
    """Créer un créneau de disponibilité."""
    try:
        # Vérifier que la ressource existe
        resource = await resource_repo.find_by_id(request.resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Ressource non trouvée")
        
        start_time = datetime.fromisoformat(request.start_time)
        end_time = datetime.fromisoformat(request.end_time)
        
        if end_time <= start_time:
            raise InvalidDateRange("La date de fin doit être après la date de début")
        
        availability = AvailabilitySlot(
            id=str(uuid4()),
            resource_id=request.resource_id,
            start_time=start_time,
            end_time=end_time,
            is_available=True,
            quantity_available=request.quantity,
            reason_if_unavailable=request.reason_if_unavailable,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        saved_availability = await availability_repo.save(availability)
        await db.commit()
        
        duration_minutes = int((saved_availability.end_time - saved_availability.start_time).total_seconds() / 60)
        
        return AvailabilitySlotResponse(
            id=saved_availability.id,
            resource_id=saved_availability.resource_id,
            start_time=saved_availability.start_time.isoformat(),
            end_time=saved_availability.end_time.isoformat(),
            is_available=saved_availability.is_available,
            quantity_available=saved_availability.quantity_available,
            reason_if_unavailable=saved_availability.reason_if_unavailable,
            duration_minutes=duration_minutes,
            created_at=saved_availability.created_at.isoformat(),
            updated_at=saved_availability.updated_at.isoformat()
        )
    except (ValueError, InvalidDateRange) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/availability/{resource_id}", response_model=List[AvailabilitySlotResponse])
async def get_availability(
    resource_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    availability_repo: PostgresAvailabilityRepository = Depends(get_availability_repository),
    resource_repo: PostgresResourceRepository = Depends(get_resource_repository)
):
    """Récupérer les créneaux de disponibilité d'une ressource."""
    # Vérifier que la ressource existe
    resource = await resource_repo.find_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Ressource non trouvée")
    
    slots = await availability_repo.find_by_resource_id(resource_id, skip=skip, limit=limit)
    return [
        AvailabilitySlotResponse(
            id=slot.id,
            resource_id=slot.resource_id,
            start_time=slot.start_time.isoformat(),
            end_time=slot.end_time.isoformat(),
            is_available=slot.is_available,
            quantity_available=slot.quantity_available,
            reason_if_unavailable=slot.reason_if_unavailable,
            duration_minutes=int((slot.end_time - slot.start_time).total_seconds() / 60),
            created_at=slot.created_at.isoformat(),
            updated_at=slot.updated_at.isoformat()
        )
        for slot in slots
    ]


@router.put("/availability/{slot_id}", response_model=AvailabilitySlotResponse)
async def update_availability(
    slot_id: str,
    request: CreateAvailabilitySlotRequest,
    availability_repo: PostgresAvailabilityRepository = Depends(get_availability_repository),
    db: AsyncSession = Depends(get_session)
):
    """Mettre à jour un créneau de disponibilité."""
    try:
        slot = await availability_repo.find_by_id(slot_id)
        if not slot:
            raise HTTPException(status_code=404, detail="Créneau non trouvé")
        
        slot.is_available = not (True if request.reason_if_unavailable else False)
        slot.quantity_available = request.quantity
        slot.reason_if_unavailable = request.reason_if_unavailable
        slot.updated_at = datetime.utcnow()
        
        updated_slot = await availability_repo.update(slot)
        await db.commit()
        
        duration_minutes = int((updated_slot.end_time - updated_slot.start_time).total_seconds() / 60)
        
        return AvailabilitySlotResponse(
            id=updated_slot.id,
            resource_id=updated_slot.resource_id,
            start_time=updated_slot.start_time.isoformat(),
            end_time=updated_slot.end_time.isoformat(),
            is_available=updated_slot.is_available,
            quantity_available=updated_slot.quantity_available,
            reason_if_unavailable=updated_slot.reason_if_unavailable,
            duration_minutes=duration_minutes,
            created_at=updated_slot.created_at.isoformat(),
            updated_at=updated_slot.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/availability/{slot_id}", status_code=204)
async def delete_availability(
    slot_id: str,
    availability_repo: PostgresAvailabilityRepository = Depends(get_availability_repository),
    db: AsyncSession = Depends(get_session)
):
    """Supprimer un créneau de disponibilité."""
    slot = await availability_repo.find_by_id(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Créneau non trouvé")
    
    await availability_repo.delete(slot_id)
    await db.commit()


# ====== Health Check ======

@router.get("/health")
async def health_check():
    """Vérifier la santé du service."""
    return {
        "service": "inventory-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
