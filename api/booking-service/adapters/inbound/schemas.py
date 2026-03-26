from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.models.booking import Booking, BookingStatus, PaymentStatus, ResourceType, SagaStatus


class CreateBookingRequest(BaseModel):
    """Represent the payload required to create a booking."""

    user_id: str
    resource_id: str
    resource_type: ResourceType
    start_time: datetime
    end_time: datetime
    party_size: int = Field(gt=0)
    quoted_price: Optional[Decimal] = Field(default=None, ge=0)
    currency: str = 'EUR'
    notes: Optional[str] = None


class CancelBookingRequest(BaseModel):
    """Represent a booking cancellation payload."""

    reason: str = 'cancelled_by_user'


class PaymentEventRequest(BaseModel):
    """Represent a payment event callback received by booking-service."""

    booking_id: str
    status: str
    payment_reference: Optional[str] = None


class InventoryEventRequest(BaseModel):
    """Represent an inventory event callback received by booking-service."""

    booking_id: str
    status: str
    hold_reference: Optional[str] = None


class BookingResponse(BaseModel):
    """Expose booking aggregate data through the public API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    resource_id: str
    resource_type: ResourceType
    start_time: datetime
    end_time: datetime
    party_size: int
    total_price: Decimal
    currency: str
    status: BookingStatus
    payment_status: PaymentStatus
    saga_status: SagaStatus
    inventory_hold_reference: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, booking: Booking) -> 'BookingResponse':
        """Build an API response from a domain booking aggregate."""
        return cls.model_validate(booking)


class HealthResponse(BaseModel):
    """Return the health status of the booking service."""

    status: str
    service: str
    integrations: dict[str, str]


class CommunicationContractsResponse(BaseModel):
    """Document the prepared REST and event contracts for other teams."""

    inventory_rest: dict
    payment_rest: dict
    published_events: list[dict]
    consumed_events: list[dict]
