from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from domain.models.booking import Booking, ResourceType


@dataclass(slots=True)
class InventoryAvailability:
    """Represent the availability answer returned by inventory."""

    available: bool
    reason: Optional[str] = None


@dataclass(slots=True)
class InventoryReservation:
    """Represent the hold created in the inventory service."""

    success: bool
    hold_reference: Optional[str] = None
    reason: Optional[str] = None


@dataclass(slots=True)
class PaymentResult:
    """Represent the response returned by payment-service."""

    status: str
    payment_reference: Optional[str] = None
    reason: Optional[str] = None


class BookingRepository(ABC):
    """Persist and query booking aggregates."""

    @abstractmethod
    async def save(self, booking: Booking) -> Booking:
        raise NotImplementedError

    @abstractmethod
    async def update(self, booking: Booking) -> Booking:
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, booking_id: str) -> Optional[Booking]:
        raise NotImplementedError

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[Booking]:
        raise NotImplementedError

    @abstractmethod
    async def find_conflicts(self, resource_id: str, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[str] = None) -> list[Booking]:
        raise NotImplementedError


class InventoryPort(ABC):
    """Define the operations required from the inventory bounded context."""

    @abstractmethod
    async def check_availability(
        self,
        *,
        resource_id: str,
        resource_type: ResourceType,
        start_time: datetime,
        end_time: datetime,
        party_size: int,
    ) -> InventoryAvailability:
        raise NotImplementedError

    @abstractmethod
    async def reserve(
        self,
        *,
        booking_id: str,
        resource_id: str,
        resource_type: ResourceType,
        start_time: datetime,
        end_time: datetime,
        party_size: int,
    ) -> InventoryReservation:
        raise NotImplementedError

    @abstractmethod
    async def release(self, *, booking_id: str, resource_id: str, hold_reference: Optional[str], reason: str) -> None:
        raise NotImplementedError


class PaymentPort(ABC):
    """Define the operations required from the payment bounded context."""

    @abstractmethod
    async def initiate_payment(
        self,
        *,
        booking_id: str,
        user_id: str,
        amount: Decimal,
        currency: str,
        resource_type: ResourceType,
    ) -> PaymentResult:
        raise NotImplementedError

    @abstractmethod
    async def cancel_payment(self, *, booking_id: str, payment_reference: Optional[str], reason: str) -> None:
        raise NotImplementedError


class AuditLogPort(ABC):
    """Send audit logs to the central log service."""

    @abstractmethod
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        details: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        raise NotImplementedError


class SystemLogPort(ABC):
    """Send structured technical logs to the log service."""

    @abstractmethod
    async def create_system_log(
        self,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        raise NotImplementedError


class EventPublisherPort(ABC):
    """Publish domain events to the outside world."""

    @abstractmethod
    async def publish(self, event_name: str, payload: dict) -> None:
        raise NotImplementedError
