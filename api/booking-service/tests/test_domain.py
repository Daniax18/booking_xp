from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domain.models.booking import BookingStatus, PaymentStatus, ResourceType, SagaStatus
from domain.ports.outbound import InventoryAvailability, InventoryReservation, PaymentResult
from domain.services.booking_service import BookingConflictError, BookingService
from domain.pricing import PricingStrategyFactory


class InMemoryBookingRepository:
    """Provide an in-memory repository for unit tests."""

    def __init__(self):
        self._bookings = {}

    async def save(self, booking):
        self._bookings[booking.id] = booking
        return booking

    async def update(self, booking):
        self._bookings[booking.id] = booking
        return booking

    async def find_by_id(self, booking_id):
        return self._bookings.get(booking_id)

    async def find_by_user_id(self, user_id):
        return [booking for booking in self._bookings.values() if booking.user_id == user_id]

    async def find_conflicts(self, resource_id, start_time, end_time, exclude_booking_id=None):
        result = []
        for booking in self._bookings.values():
            if booking.id == exclude_booking_id:
                continue
            if booking.resource_id != resource_id:
                continue
            if booking.status == BookingStatus.CANCELLED:
                continue
            if booking.overlaps(start_time, end_time):
                result.append(booking)
        return result


class FakeInventoryPort:
    """Control inventory responses in unit tests."""

    def __init__(self, available=True, reserve_success=True):
        self.available = available
        self.reserve_success = reserve_success
        self.release_calls = []

    async def check_availability(self, **kwargs):
        return InventoryAvailability(available=self.available, reason=None if self.available else 'unavailable')

    async def reserve(self, **kwargs):
        if self.reserve_success:
            return InventoryReservation(success=True, hold_reference='hold-123')
        return InventoryReservation(success=False, reason='reservation_failed')

    async def release(self, **kwargs):
        self.release_calls.append(kwargs)


class FakePaymentPort:
    """Control payment responses in unit tests."""

    def __init__(self, status='PAID'):
        self.status = status
        self.cancel_calls = []

    async def initiate_payment(self, **kwargs):
        return PaymentResult(status=self.status, payment_reference='pay-123', reason='payment_failed')

    async def cancel_payment(self, **kwargs):
        self.cancel_calls.append(kwargs)


class FakeAuditLogPort:
    """Record audit logs emitted by the domain service."""

    def __init__(self):
        self.calls = []

    async def create_audit_log(self, **kwargs):
        self.calls.append(kwargs)


class FakeSystemLogPort:
    """Record system logs emitted by the domain service."""

    def __init__(self):
        self.calls = []

    async def create_system_log(self, **kwargs):
        self.calls.append(kwargs)


class FakeEventPublisher:
    """Record domain events published by the application service."""

    def __init__(self):
        self.calls = []

    async def publish(self, event_name, payload):
        self.calls.append({'event_name': event_name, 'payload': payload})


@pytest.fixture
def booking_dependencies():
    """Build the booking service with deterministic fake collaborators."""
    repository = InMemoryBookingRepository()
    inventory = FakeInventoryPort()
    payment = FakePaymentPort()
    audit = FakeAuditLogPort()
    system = FakeSystemLogPort()
    events = FakeEventPublisher()
    service = BookingService(
        booking_repository=repository,
        inventory_port=inventory,
        payment_port=payment,
        audit_log_port=audit,
        system_log_port=system,
        event_publisher=events,
        pricing_strategy_factory=PricingStrategyFactory(),
    )
    return service, repository, inventory, payment, audit, system, events


@pytest.mark.asyncio
async def test_create_booking_confirms_and_publishes_observability(booking_dependencies):
    """Ensure the happy path reserves inventory, charges payment, and confirms the booking."""
    service, repository, inventory, payment, audit, system, events = booking_dependencies
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)

    booking = await service.create_booking(
        user_id='user-1',
        resource_id='resource-1',
        resource_type=ResourceType.VENUE,
        start_time=start_time,
        end_time=end_time,
        party_size=10,
    )

    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == PaymentStatus.PAID
    assert booking.saga_status == SagaStatus.COMPLETED
    assert booking.payment_reference == 'pay-123'
    assert booking.inventory_hold_reference == 'hold-123'
    assert len(audit.calls) >= 3
    assert len(system.calls) >= 3
    assert any(call['event_name'] == 'booking.confirmed' for call in events.calls)


@pytest.mark.asyncio
async def test_create_booking_rejects_overlap(booking_dependencies):
    """Ensure the availability specification blocks overlapping bookings."""
    service, repository, inventory, payment, audit, system, events = booking_dependencies
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)

    await service.create_booking(
        user_id='user-1',
        resource_id='resource-1',
        resource_type=ResourceType.RESTAURANT_TABLE,
        start_time=start_time,
        end_time=end_time,
        party_size=4,
        quoted_price=Decimal('100.00'),
    )

    with pytest.raises(BookingConflictError):
        await service.create_booking(
            user_id='user-2',
            resource_id='resource-1',
            resource_type=ResourceType.RESTAURANT_TABLE,
            start_time=start_time + timedelta(minutes=30),
            end_time=end_time + timedelta(minutes=30),
            party_size=2,
        )


@pytest.mark.asyncio
async def test_failed_payment_releases_inventory_and_cancels_booking():
    """Ensure the saga compensates inventory when payment fails."""
    repository = InMemoryBookingRepository()
    inventory = FakeInventoryPort()
    payment = FakePaymentPort(status='FAILED')
    service = BookingService(
        booking_repository=repository,
        inventory_port=inventory,
        payment_port=payment,
        audit_log_port=FakeAuditLogPort(),
        system_log_port=FakeSystemLogPort(),
        event_publisher=FakeEventPublisher(),
        pricing_strategy_factory=PricingStrategyFactory(),
    )
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(days=1)

    booking = await service.create_booking(
        user_id='user-1',
        resource_id='room-9',
        resource_type=ResourceType.HOTEL_ROOM,
        start_time=start_time,
        end_time=end_time,
        party_size=2,
    )

    assert booking.status == BookingStatus.CANCELLED
    assert booking.payment_status == PaymentStatus.FAILED
    assert inventory.release_calls[0]['booking_id'] == booking.id


@pytest.mark.asyncio
async def test_payment_event_confirms_pending_booking(booking_dependencies):
    """Ensure asynchronous payment events can confirm a pending booking."""
    service, repository, inventory, payment, audit, system, events = booking_dependencies
    payment.status = 'PENDING'
    start_time = datetime.now(timezone.utc) + timedelta(days=2)
    end_time = start_time + timedelta(hours=3)

    booking = await service.create_booking(
        user_id='user-1',
        resource_id='venue-77',
        resource_type=ResourceType.VENUE,
        start_time=start_time,
        end_time=end_time,
        party_size=25,
    )
    updated = await service.handle_payment_event(booking_id=booking.id, status='PAID', payment_reference='pay-999')

    assert booking.status == BookingStatus.PENDING
    assert updated.status == BookingStatus.CONFIRMED
    assert updated.payment_reference == 'pay-999'
