# application/dtos.py
"""DTOs (Data Transfer Objects) pour l'API."""
from dataclasses import dataclass
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

@dataclass
class CreateResourceRequest:
    """DTO de requête pour créer une ressource."""
    name: str
    type: ResourceTypeEnum
    description: str
    capacity: int
    location: str
    price: float


@dataclass
class CreateResourceResponse:
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


@dataclass
class UpdateResourceRequest:
    """DTO de requête pour mettre à jour une ressource."""
    name: Optional[str] = None
    type: Optional[ResourceTypeEnum] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


@dataclass
class ResourceResponse:
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


@dataclass
class ResourceListResponse:
    """DTO de réponse pour une liste de ressources."""
    resources: List[ResourceResponse]
    total: int


# ====== DTOs pour la Disponibilité ======

@dataclass
class CreateAvailabilitySlotRequest:
    """DTO de requête pour créer un créneau de disponibilité."""
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1
    reason_if_unavailable: Optional[str] = None


@dataclass
class AvailabilitySlotResponse:
    """DTO de réponse pour un créneau de disponibilité."""
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
    """DTO de requête pour vérifier la disponibilité."""
    resource_id: str
    start_time: str
    end_time: str
    quantity: int = 1


@dataclass
class AvailabilityCheckResponse:
    """DTO de réponse pour une vérification de disponibilité."""
    resource_id: str
    is_available: bool
    period: dict
    quantity_required: int


@dataclass
class AvailabilityListResponse:
    """DTO de réponse pour une liste de créneaux de disponibilité."""
    resource_id: str
    period: dict
    available_slots: List[AvailabilitySlotResponse]
    total_available_slots: int
    total_available_minutes: int


# ====== DTOs pour les Erreurs ======

@dataclass
class ErrorResponse:
    """DTO de réponse pour les erreurs."""
    error: str
    message: str
    timestamp: str
    request_id: Optional[str] = None


@dataclass
class ValidationErrorResponse:
    """DTO de réponse pour les erreurs de validation."""
    error: str
    message: str
    details: dict
    timestamp: str
    request_id: Optional[str] = None
