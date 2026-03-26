# adapters/inbound/schemas.py
"""Pydantic schemas pour l'API - Validation des requêtes/réponses."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ResourceTypeEnum(str, Enum):
    """Énumération des types de ressources."""
    ROOM = "room"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    SERVICE = "service"


# ====== DTOs pour les Ressources ======

class CreateResourceRequest(BaseModel):
    """DTO de requête pour créer une ressource."""
    name: str = Field(..., min_length=1, max_length=255, description="Nom de la ressource")
    type: ResourceTypeEnum = Field(..., description="Type de ressource")
    description: str = Field(default="", max_length=1000, description="Description détaillée")
    capacity: int = Field(..., gt=0, description="Capacité (doit être positive)")
    location: str = Field(..., min_length=1, max_length=500, description="Localisation")
    price: float = Field(..., ge=0, description="Prix (doit être positif ou zéro)")


class CreateResourceResponse(BaseModel):
    """DTO de réponse pour une ressource créée."""
    id: str
    name: str
    type: str
    description: str
    capacity: int
    location: str
    price: float
    is_active: bool
    created_at: str


class UpdateResourceRequest(BaseModel):
    """DTO de requête pour mettre à jour une ressource."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[ResourceTypeEnum] = None
    description: Optional[str] = Field(None, max_length=1000)
    capacity: Optional[int] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ResourceResponse(BaseModel):
    """DTO de réponse pour une ressource."""
    id: str
    name: str
    type: str
    description: str
    capacity: int
    location: str
    price: float
    is_active: bool
    created_at: str
    updated_at: str


class ResourceListResponse(BaseModel):
    """DTO de réponse pour une liste de ressources."""
    resources: List[ResourceResponse]
    total: int


# ====== DTOs pour la Disponibilité ======

class CreateAvailabilitySlotRequest(BaseModel):
    """DTO de requête pour créer un créneau de disponibilité."""
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1
    reason_if_unavailable: Optional[str] = None


class AvailabilitySlotResponse(BaseModel):
    """DTO de réponse pour un créneau de disponibilité."""
    id: str
    resource_id: str
    start_time: str
    end_time: str
    is_available: bool
    quantity_available: int
    reason_if_unavailable: Optional[str] = None
    duration_minutes: int
    created_at: str
    updated_at: str


class GetAvailabilityRequest(BaseModel):
    """DTO de requête pour vérifier la disponibilité."""
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1


class AvailabilityCheckResponse(BaseModel):
    """DTO de réponse pour une vérification de disponibilité."""
    resource_id: str
    is_available: bool
    period: dict
    quantity_required: int


class AvailabilityListResponse(BaseModel):
    """DTO de réponse pour une liste de créneaux de disponibilité."""
    resource_id: str
    period: dict
    available_slots: List[AvailabilitySlotResponse]
    total_available_slots: int
    total_available_minutes: int


# ====== DTOs pour les Erreurs ======

class ErrorResponse(BaseModel):
    """DTO de réponse pour les erreurs."""
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """DTO de réponse pour les erreurs de validation."""
    error: str
    message: str
    details: dict
    timestamp: str
    request_id: Optional[str] = None
