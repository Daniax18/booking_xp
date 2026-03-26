from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4


class ResourceType(str, Enum):
    """Represent the kind of reservable resource handled by the service."""

    HOTEL_ROOM = 'HOTEL_ROOM'
    RESTAURANT_TABLE = 'RESTAURANT_TABLE'
    VENUE = 'VENUE'


class BookingStatus(str, Enum):
    """Represent the public lifecycle of a booking."""

    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'


class PaymentStatus(str, Enum):
    """Represent the payment state attached to a booking."""

    PENDING = 'PENDING'
    PAID = 'PAID'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'


class SagaStatus(str, Enum):
    """Represent the orchestration progress across inventory and payment."""

    STARTED = 'STARTED'
    INVENTORY_RESERVED = 'INVENTORY_RESERVED'
    PAYMENT_PENDING = 'PAYMENT_PENDING'
    COMPLETED = 'COMPLETED'
    COMPENSATED = 'COMPENSATED'
    FAILED = 'FAILED'


@dataclass(slots=True)
class Booking:
    """Aggregate root for a reservation handled by the booking service."""

    user_id: str
    resource_id: str
    resource_type: ResourceType
    start_time: datetime
    end_time: datetime
    party_size: int
    total_price: Decimal
    id: str = field(default_factory=lambda: str(uuid4()))
    status: BookingStatus = BookingStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    saga_status: SagaStatus = SagaStatus.STARTED
    currency: str = 'EUR'
    inventory_hold_reference: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate core invariants for the aggregate."""
        if isinstance(self.resource_type, str):
            self.resource_type = ResourceType(self.resource_type)
        if isinstance(self.status, str):
            self.status = BookingStatus(self.status)
        if isinstance(self.payment_status, str):
            self.payment_status = PaymentStatus(self.payment_status)
        if isinstance(self.saga_status, str):
            self.saga_status = SagaStatus(self.saga_status)
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        if self.party_size <= 0:
            raise ValueError('party_size must be greater than zero')
        if Decimal(self.total_price) < Decimal('0'):
            raise ValueError('total_price cannot be negative')
        self.total_price = Decimal(self.total_price).quantize(Decimal('0.01'))
        self.touch()

    def touch(self) -> None:
        """Refresh the update timestamp after a state transition."""
        self.updated_at = datetime.now(timezone.utc)

    def overlaps(self, other_start: datetime, other_end: datetime) -> bool:
        """Return whether the booking overlaps another requested time range."""
        return self.start_time < other_end and self.end_time > other_start

    def mark_inventory_reserved(self, hold_reference: str) -> None:
        """Record that inventory accepted the temporary reservation."""
        self.inventory_hold_reference = hold_reference
        self.saga_status = SagaStatus.INVENTORY_RESERVED
        self.touch()

    def mark_payment_pending(self, payment_reference: str) -> None:
        """Record that a payment transaction was created but not finalized yet."""
        self.payment_reference = payment_reference
        self.payment_status = PaymentStatus.PENDING
        self.saga_status = SagaStatus.PAYMENT_PENDING
        self.touch()

    def confirm(self, payment_reference: Optional[str] = None) -> None:
        """Confirm the booking after successful payment and reserved inventory."""
        if payment_reference:
            self.payment_reference = payment_reference
        self.status = BookingStatus.CONFIRMED
        self.payment_status = PaymentStatus.PAID
        self.saga_status = SagaStatus.COMPLETED
        self.touch()

    def fail_payment(self, payment_reference: Optional[str] = None) -> None:
        """Mark the booking as cancelled because payment failed."""
        if payment_reference:
            self.payment_reference = payment_reference
        self.status = BookingStatus.CANCELLED
        self.payment_status = PaymentStatus.FAILED
        self.saga_status = SagaStatus.FAILED
        self.touch()

    def cancel(self) -> None:
        """Cancel a booking and mark the saga as compensated."""
        self.status = BookingStatus.CANCELLED
        if self.payment_status == PaymentStatus.PAID:
            self.payment_status = PaymentStatus.REFUNDED
        self.saga_status = SagaStatus.COMPENSATED
        self.touch()
