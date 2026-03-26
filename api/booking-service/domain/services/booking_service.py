from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from domain.models.booking import Booking, BookingStatus, ResourceType
from domain.ports.inbound import BookingInputPort
from domain.ports.outbound import (
    AuditLogPort,
    BookingRepository,
    EventPublisherPort,
    InventoryPort,
    PaymentPort,
    PaymentResult,
    SystemLogPort,
)
from domain.pricing import PricingStrategyFactory
from domain.specifications import BookingTimeRangeSpecification, PartySizeSpecification, ResourceAvailabilitySpecification


class BookingError(Exception):
    """Base error type for the booking application service."""


class BookingConflictError(BookingError):
    """Raise when the requested booking collides with another reservation."""


class BookingNotFoundError(BookingError):
    """Raise when a booking cannot be found."""


class BookingService(BookingInputPort):
    """Orchestrate booking creation, compensation, and external collaborations."""

    def __init__(
        self,
        *,
        booking_repository: BookingRepository,
        inventory_port: InventoryPort,
        payment_port: PaymentPort,
        audit_log_port: AuditLogPort,
        system_log_port: SystemLogPort,
        event_publisher: EventPublisherPort,
        pricing_strategy_factory: PricingStrategyFactory,
    ) -> None:
        self._booking_repository = booking_repository
        self._inventory_port = inventory_port
        self._payment_port = payment_port
        self._audit_log_port = audit_log_port
        self._system_log_port = system_log_port
        self._event_publisher = event_publisher
        self._pricing_strategy_factory = pricing_strategy_factory
        self._time_specification = BookingTimeRangeSpecification()
        self._party_specification = PartySizeSpecification()

    async def _emit_observability(self, booking: Booking, action: str, details: Optional[dict] = None) -> None:
        """Send audit log, system log, and domain event on a best-effort basis."""
        payload = details or {}
        try:
            await self._audit_log_port.create_audit_log(
                user_id=booking.user_id,
                action=action,
                entity='booking',
                entity_id=booking.id,
                details=payload,
            )
            await self._system_log_port.create_system_log(
                level='INFO',
                message=f'booking-service.{action.lower()}',
                metadata={
                    'booking_id': booking.id,
                    'resource_id': booking.resource_id,
                    'status': booking.status.value,
                    'payment_status': booking.payment_status.value,
                    **payload,
                },
            )
            await self._event_publisher.publish(
                event_name=f'booking.{action.lower()}',
                payload={
                    'booking_id': booking.id,
                    'user_id': booking.user_id,
                    'resource_id': booking.resource_id,
                    'resource_type': booking.resource_type.value,
                    'status': booking.status.value,
                    'payment_status': booking.payment_status.value,
                    **payload,
                },
            )
        except Exception:
            return

    async def _get_existing_booking(self, booking_id: str) -> Booking:
        """Return a booking or raise a domain-specific not found error."""
        booking = await self._booking_repository.find_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError('Booking not found')
        return booking

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
        """Create a booking and run the reservation plus payment saga."""
        if not self._time_specification.is_satisfied_by(start_time, end_time):
            raise BookingError('Invalid booking time range')
        if not self._party_specification.is_satisfied_by(party_size):
            raise BookingError('Invalid party size')

        conflicts = await self._booking_repository.find_conflicts(resource_id, start_time, end_time)
        availability_spec = ResourceAvailabilitySpecification(conflicts)
        if not availability_spec.is_satisfied_by(resource_id, start_time, end_time):
            raise BookingConflictError('Resource already booked for this period')

        remote_availability = await self._inventory_port.check_availability(
            resource_id=resource_id,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
            party_size=party_size,
        )
        if not remote_availability.available:
            raise BookingConflictError(remote_availability.reason or 'Inventory service reports no availability')

        price_strategy = self._pricing_strategy_factory.get_strategy(resource_type)
        total_price = price_strategy.calculate(
            start_time=start_time,
            end_time=end_time,
            party_size=party_size,
            quoted_price=quoted_price,
        )
        booking = Booking(
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
            party_size=party_size,
            total_price=total_price,
            currency=currency,
            notes=notes,
        )
        booking = await self._booking_repository.save(booking)
        await self._emit_observability(booking, 'CREATED', {'stage': 'persisted'})

        inventory_reservation = await self._inventory_port.reserve(
            booking_id=booking.id,
            resource_id=resource_id,
            resource_type=resource_type,
            start_time=start_time,
            end_time=end_time,
            party_size=party_size,
        )
        if not inventory_reservation.success:
            booking.cancel()
            booking = await self._booking_repository.update(booking)
            await self._emit_observability(booking, 'CANCELLED', {'reason': inventory_reservation.reason or 'inventory_reservation_failed'})
            raise BookingConflictError(inventory_reservation.reason or 'Unable to reserve inventory')

        booking.mark_inventory_reserved(inventory_reservation.hold_reference or '')
        booking = await self._booking_repository.update(booking)
        await self._emit_observability(booking, 'INVENTORY_RESERVED', {'hold_reference': booking.inventory_hold_reference})

        payment_result = await self._payment_port.initiate_payment(
            booking_id=booking.id,
            user_id=user_id,
            amount=booking.total_price,
            currency=booking.currency,
            resource_type=booking.resource_type,
        )
        return await self._apply_payment_result(booking, payment_result)

    async def _apply_payment_result(self, booking: Booking, payment_result: PaymentResult) -> Booking:
        """Apply payment response and compensation rules to the booking."""
        normalized_status = payment_result.status.upper()
        if normalized_status == 'PAID':
            booking.confirm(payment_result.payment_reference)
            booking = await self._booking_repository.update(booking)
            await self._emit_observability(booking, 'CONFIRMED', {'payment_reference': booking.payment_reference})
            return booking

        if normalized_status == 'PENDING':
            booking.mark_payment_pending(payment_result.payment_reference or '')
            booking = await self._booking_repository.update(booking)
            await self._emit_observability(booking, 'PAYMENT_PENDING', {'payment_reference': booking.payment_reference})
            return booking

        await self._inventory_port.release(
            booking_id=booking.id,
            resource_id=booking.resource_id,
            hold_reference=booking.inventory_hold_reference,
            reason=payment_result.reason or 'payment_failed',
        )
        booking.fail_payment(payment_result.payment_reference)
        booking = await self._booking_repository.update(booking)
        await self._emit_observability(booking, 'PAYMENT_FAILED', {'reason': payment_result.reason or 'payment_failed'})
        return booking

    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Return one booking by identifier."""
        return await self._booking_repository.find_by_id(booking_id)

    async def list_bookings_for_user(self, user_id: str) -> list[Booking]:
        """Return all bookings owned by a given user."""
        return await self._booking_repository.find_by_user_id(user_id)

    async def cancel_booking(self, booking_id: str, reason: str) -> Booking:
        """Cancel a booking and trigger compensating actions on collaborators."""
        booking = await self._get_existing_booking(booking_id)
        if booking.status == BookingStatus.CANCELLED:
            return booking

        await self._inventory_port.release(
            booking_id=booking.id,
            resource_id=booking.resource_id,
            hold_reference=booking.inventory_hold_reference,
            reason=reason,
        )
        await self._payment_port.cancel_payment(
            booking_id=booking.id,
            payment_reference=booking.payment_reference,
            reason=reason,
        )
        booking.cancel()
        booking = await self._booking_repository.update(booking)
        await self._emit_observability(booking, 'CANCELLED', {'reason': reason})
        return booking

    async def handle_payment_event(self, booking_id: str, status: str, payment_reference: Optional[str] = None) -> Booking:
        """Apply an asynchronous payment event coming from the payment service."""
        booking = await self._get_existing_booking(booking_id)
        normalized_status = status.upper()
        if normalized_status == 'PAID':
            booking.confirm(payment_reference)
            booking = await self._booking_repository.update(booking)
            await self._emit_observability(booking, 'CONFIRMED', {'source': 'payment_event'})
            return booking

        if normalized_status == 'FAILED':
            await self._inventory_port.release(
                booking_id=booking.id,
                resource_id=booking.resource_id,
                hold_reference=booking.inventory_hold_reference,
                reason='payment_event_failed',
            )
            booking.fail_payment(payment_reference)
            booking = await self._booking_repository.update(booking)
            await self._emit_observability(booking, 'PAYMENT_FAILED', {'source': 'payment_event'})
            return booking

        booking.mark_payment_pending(payment_reference or booking.payment_reference or '')
        booking = await self._booking_repository.update(booking)
        await self._emit_observability(booking, 'PAYMENT_PENDING', {'source': 'payment_event'})
        return booking

    async def handle_inventory_event(self, booking_id: str, status: str, hold_reference: Optional[str] = None) -> Booking:
        """Apply an asynchronous inventory event coming from the inventory service."""
        booking = await self._get_existing_booking(booking_id)
        normalized_status = status.upper()
        if normalized_status == 'RESERVED':
            booking.mark_inventory_reserved(hold_reference or booking.inventory_hold_reference or '')
            booking = await self._booking_repository.update(booking)
            await self._emit_observability(booking, 'INVENTORY_RESERVED', {'source': 'inventory_event'})
            return booking

        booking.cancel()
        booking = await self._booking_repository.update(booking)
        await self._emit_observability(booking, 'CANCELLED', {'source': 'inventory_event', 'reason': status})
        return booking
