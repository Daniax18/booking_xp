"""Schemas Pydantic pour l'API de l'Inventory Service."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResourceTypeEnum(str, Enum):
    """Enum des types de ressources supportes."""

    ROOM = "room"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    SERVICE = "service"


class CreateResourceRequest(BaseModel):
    """Representer le payload de creation d'une ressource."""

    name: str = Field(..., min_length=1, max_length=255, description="Nom de la ressource")
    type: ResourceTypeEnum = Field(..., description="Type de ressource")
    description: str = Field(default="", max_length=1000, description="Description detaillee")
    capacity: int = Field(..., gt=0, description="Capacite strictement positive")
    location: str = Field(..., min_length=1, max_length=500, description="Localisation")
    price: float = Field(..., ge=0, description="Prix positif ou nul")


class CreateResourceResponse(BaseModel):
    """Representer la reponse apres creation d'une ressource."""

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
    """Representer les champs modifiables d'une ressource."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[ResourceTypeEnum] = None
    description: Optional[str] = Field(None, max_length=1000)
    capacity: Optional[int] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ResourceResponse(BaseModel):
    """Representer une ressource retournee par l'API."""

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
    """Representer une liste de ressources."""

    resources: List[ResourceResponse]
    total: int


class CreateAvailabilitySlotRequest(BaseModel):
    """Representer le payload de creation d'un creneau."""

    resource_id: str
    start_time: str
    end_time: str
    quantity: int = Field(1, gt=0)
    reason_if_unavailable: Optional[str] = Field(None, max_length=1000)


class UpdateAvailabilityRequest(BaseModel):
    """Representer les champs modifiables d'un creneau."""

    quantity: Optional[int] = Field(None, gt=0, description="Quantite disponible")
    reason_if_unavailable: Optional[str] = Field(
        None,
        max_length=1000,
        description="Raison d'indisponibilite si le creneau est indisponible",
    )


class AvailabilitySlotResponse(BaseModel):
    """Representer un creneau de disponibilite retourne par l'API."""

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
    """Representer une requete de verification de disponibilite."""

    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1


class AvailabilityCheckResponse(BaseModel):
    """Representer le resultat d'une verification de disponibilite."""

    resource_id: str
    is_available: bool
    period: dict
    quantity_required: int


class AvailabilityListResponse(BaseModel):
    """Representer une liste de creneaux de disponibilite."""

    resource_id: str
    period: dict
    available_slots: List[AvailabilitySlotResponse]
    total_available_slots: int
    total_available_minutes: int


class ErrorResponse(BaseModel):
    """Representer une reponse d'erreur generique."""

    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Representer une erreur de validation detaillee."""

    error: str
    message: str
    details: dict
    timestamp: str
    request_id: Optional[str] = None
