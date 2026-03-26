"""Schemas Pydantic pour l'API de l'Inventory Service."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ResourceTypeEnum(str, Enum):
    """Expose the business resource types expected by the booking platform."""

    HOTEL_ROOM = 'HOTEL_ROOM'
    RESTAURANT_TABLE = 'RESTAURANT_TABLE'
    VENUE = 'VENUE'


class CreateResourceRequest(BaseModel):
    """Representer le payload de creation d'une ressource."""

    name: str = Field(..., min_length=1, max_length=255, description='Nom de la ressource')
    type: ResourceTypeEnum = Field(..., description='Type metier de la ressource')
    description: str = Field(default='', max_length=1000, description='Description detaillee')
    capacity: int = Field(..., gt=0, description='Capacite strictement positive')
    location: str = Field(..., min_length=1, max_length=500, description='Localisation')
    price: float = Field(..., ge=0, description='Prix positif ou nul')


class CreateResourceResponse(BaseModel):
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
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[ResourceTypeEnum] = None
    description: Optional[str] = Field(None, max_length=1000)
    capacity: Optional[int] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ResourceResponse(BaseModel):
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
    resources: List[ResourceResponse]
    total: int


class CreateAvailabilitySlotRequest(BaseModel):
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = Field(1, gt=0)
    reason_if_unavailable: Optional[str] = Field(None, max_length=1000)


class UpdateAvailabilityRequest(BaseModel):
    """Allow zero when a slot becomes fully reserved."""

    quantity: Optional[int] = Field(None, ge=0, description='Quantite disponible restante')
    reason_if_unavailable: Optional[str] = Field(
        None,
        max_length=1000,
        description='Raison d indisponibilite si le creneau est indisponible',
    )


class AvailabilitySlotResponse(BaseModel):
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
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1


class AvailabilityCheckResponse(BaseModel):
    resource_id: str
    is_available: bool
    period: dict
    quantity_required: int


class AvailabilityListResponse(BaseModel):
    resource_id: str
    period: dict
    available_slots: List[AvailabilitySlotResponse]
    total_available_slots: int
    total_available_minutes: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    error: str
    message: str
    details: dict
    timestamp: str
    request_id: Optional[str] = None
