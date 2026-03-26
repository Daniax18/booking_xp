"""DTOs (Data Transfer Objects) pour l'API."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ResourceTypeEnum(str, Enum):
    """Expose the business resource types used across the reservation platform."""

    HOTEL_ROOM = 'HOTEL_ROOM'
    RESTAURANT_TABLE = 'RESTAURANT_TABLE'
    VENUE = 'VENUE'


@dataclass
class CreateResourceRequest:
    """DTO de requete pour creer une ressource."""
    name: str
    type: ResourceTypeEnum
    description: str
    capacity: int
    location: str
    price: float


@dataclass
class CreateResourceResponse:
    """DTO de reponse pour une ressource creee."""
    id: str
    name: str
    type: str
    description: str
    capacity: int
    location: str
    price: float
    is_active: bool
    created_at: str


@dataclass
class UpdateResourceRequest:
    """DTO de requete pour mettre a jour une ressource."""
    name: Optional[str] = None
    type: Optional[ResourceTypeEnum] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


@dataclass
class ResourceResponse:
    """DTO de reponse pour une ressource."""
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


@dataclass
class ResourceListResponse:
    """DTO de reponse pour une liste de ressources."""
    resources: List[ResourceResponse]
    total: int


@dataclass
class CreateAvailabilitySlotRequest:
    """DTO de requete pour creer un creneau de disponibilite."""
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1
    reason_if_unavailable: Optional[str] = None


@dataclass
class AvailabilitySlotResponse:
    """DTO de reponse pour un creneau de disponibilite."""
    id: str
    resource_id: str
    start_time: str
    end_time: str
    is_available: bool
    quantity_available: int
    reason_if_unavailable: Optional[str]
    duration_minutes: int
    created_at: str
    updated_at: str


@dataclass
class GetAvailabilityRequest:
    """DTO de requete pour verifier la disponibilite."""
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1


@dataclass
class AvailabilityCheckResponse:
    """DTO de reponse pour une verification de disponibilite."""
    resource_id: str
    is_available: bool
    period: dict
    quantity_required: int


@dataclass
class AvailabilityListResponse:
    """DTO de reponse pour une liste de creneaux de disponibilite."""
    resource_id: str
    period: dict
    available_slots: List[AvailabilitySlotResponse]
    total_available_slots: int
    total_available_minutes: int


@dataclass
class ErrorResponse:
    """DTO de reponse pour les erreurs."""
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None


@dataclass
class ValidationErrorResponse:
    """DTO de reponse pour les erreurs de validation."""
    error: str
    message: str
    details: dict
    timestamp: str
    request_id: Optional[str] = None
