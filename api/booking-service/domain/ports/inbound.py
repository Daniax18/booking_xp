from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from domain.models.booking import Booking, ResourceType


class BookingInputPort(ABC):
    """Describe the booking use cases exposed to inbound adapters."""

    @abstractmethod
    async def create_booking(
        self,
        *,
        user_id: str,
        resource_id: str,
        resource_type: ResourceType,
        start_time: datetime,
        end_time: datetime,
        party_size: int,
        quoted_price: Optional[Decimal] = None,
        currency: str = 'EUR',
        notes: Optional[str] = None,
    ) -> Booking:
        """Create a booking and orchestrate inventory and payment."""
        raise NotImplementedError

    @abstractmethod
    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Fetch one booking by its identifier."""
        raise NotImplementedError

    @abstractmethod
    async def list_bookings_for_user(self, user_id: str) -> list[Booking]:
        """List bookings belonging to one user."""
        raise NotImplementedError

    @abstractmethod
    async def cancel_booking(self, booking_id: str, reason: str) -> Booking:
        """Cancel an existing booking and trigger compensating actions."""
        raise NotImplementedError

    @abstractmethod
    async def handle_payment_event(self, booking_id: str, status: str, payment_reference: Optional[str] = None) -> Booking:
        """Update a booking from a payment-service event or callback."""
        raise NotImplementedError

    @abstractmethod
    async def handle_inventory_event(self, booking_id: str, status: str, hold_reference: Optional[str] = None) -> Booking:
        """Update a booking from an inventory-service event or callback."""
        raise NotImplementedError
