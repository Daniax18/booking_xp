from datetime import datetime

import httpx
import structlog

from domain.models.booking import ResourceType
from domain.ports.outbound import InventoryAvailability, InventoryPort, InventoryReservation
from infrastructure.middleware import CORRELATION_ID_HEADER, get_correlation_id


logger = structlog.get_logger(__name__)


class HttpInventoryClient(InventoryPort):
    """Integrate booking-service with the public inventory-service API."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0, integration_mode: str = 'stub', transport=None):
        self._base_url = base_url.rstrip('/')
        self._timeout_seconds = timeout_seconds
        self._integration_mode = integration_mode.lower()
        self._transport = transport

    def _headers(self) -> dict:
        """Build outbound headers with the current correlation identifier."""
        correlation_id = get_correlation_id()
        return {CORRELATION_ID_HEADER: correlation_id} if correlation_id else {}

    async def _get_resource(self, resource_id: str) -> dict:
        """Fetch a resource from inventory-service."""
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.get(f'{self._base_url}/api/v1/inventory/resources/{resource_id}')
            response.raise_for_status()
            return response.json()

    async def _get_slots(self, resource_id: str) -> list[dict]:
        """Fetch availability slots for the given resource."""
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.get(f'{self._base_url}/api/v1/inventory/availability/{resource_id}')
            response.raise_for_status()
            return response.json()

    async def _update_slot(self, slot_id: str, quantity: int, reason_if_unavailable: str | None) -> dict:
        """Update one inventory availability slot."""
        payload = {
            'quantity': quantity,
            'reason_if_unavailable': reason_if_unavailable,
        }
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.put(f'{self._base_url}/api/v1/inventory/availability/{slot_id}', json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _find_matching_slot(slots: list[dict], start_time: datetime, end_time: datetime) -> dict | None:
        """Return the first slot that fully covers the requested booking period."""
        for slot in slots:
            slot_start = datetime.fromisoformat(slot['start_time'])
            slot_end = datetime.fromisoformat(slot['end_time'])
            if slot_start <= start_time and slot_end >= end_time:
                return slot
        return None

    async def check_availability(self, *, resource_id: str, resource_type: ResourceType, start_time: datetime, end_time: datetime, party_size: int) -> InventoryAvailability:
        """Check resource capacity and slot availability via the real inventory routes."""
        if self._integration_mode == 'stub':
            logger.info('booking.integration.inventory.check.stub', resource_id=resource_id, resource_type=resource_type.value)
            return InventoryAvailability(available=True)

        logger.info('booking.integration.inventory.check.request', resource_id=resource_id, resource_type=resource_type.value)
        try:
            resource = await self._get_resource(resource_id)
            slots = await self._get_slots(resource_id)
        except httpx.HTTPStatusError as exc:
            logger.warning('booking.integration.inventory.check.http_error', status_code=exc.response.status_code, resource_id=resource_id)
            return InventoryAvailability(available=False, reason='inventory_resource_not_found')

        if not resource.get('is_active', True):
            return InventoryAvailability(available=False, reason='resource_inactive')

        if party_size > int(resource.get('capacity', 0)):
            return InventoryAvailability(available=False, reason='party_size_exceeds_capacity')

        matching_slot = self._find_matching_slot(slots, start_time, end_time)
        if not matching_slot:
            return InventoryAvailability(available=False, reason='no_matching_slot')

        if not matching_slot.get('is_available', False):
            return InventoryAvailability(available=False, reason=matching_slot.get('reason_if_unavailable') or 'slot_unavailable')

        if int(matching_slot.get('quantity_available', 0)) < 1:
            return InventoryAvailability(available=False, reason='slot_exhausted')

        return InventoryAvailability(available=True)

    async def reserve(self, *, booking_id: str, resource_id: str, resource_type: ResourceType, start_time: datetime, end_time: datetime, party_size: int) -> InventoryReservation:
        """Reserve capacity by decrementing the matching inventory slot quantity."""
        if self._integration_mode == 'stub':
            hold_reference = f'inv-{booking_id}'
            logger.info('booking.integration.inventory.reserve.stub', booking_id=booking_id, hold_reference=hold_reference)
            return InventoryReservation(success=True, hold_reference=hold_reference)

        logger.info('booking.integration.inventory.reserve.request', booking_id=booking_id, resource_id=resource_id)
        slots = await self._get_slots(resource_id)
        matching_slot = self._find_matching_slot(slots, start_time, end_time)
        if not matching_slot:
            return InventoryReservation(success=False, reason='no_matching_slot')

        current_quantity = int(matching_slot.get('quantity_available', 0))
        if (not matching_slot.get('is_available', False)) or current_quantity < 1:
            return InventoryReservation(success=False, reason='slot_unavailable')

        new_quantity = current_quantity - 1
        reason_if_unavailable = 'reserved_by_booking_service' if new_quantity == 0 else None
        await self._update_slot(matching_slot['id'], new_quantity, reason_if_unavailable)
        logger.info('booking.integration.inventory.reserve.response', booking_id=booking_id, slot_id=matching_slot['id'], new_quantity=new_quantity)
        return InventoryReservation(success=True, hold_reference=matching_slot['id'])

    async def release(self, *, booking_id: str, resource_id: str, hold_reference: str | None, reason: str) -> None:
        """Release a previous reservation by incrementing the tracked slot quantity."""
        if self._integration_mode == 'stub':
            logger.info('booking.integration.inventory.release.stub', booking_id=booking_id, hold_reference=hold_reference, reason=reason)
            return

        if not hold_reference:
            logger.warning('booking.integration.inventory.release.skipped', booking_id=booking_id, reason='missing_hold_reference')
            return

        slots = await self._get_slots(resource_id)
        slot = next((item for item in slots if item['id'] == hold_reference), None)
        if not slot:
            logger.warning('booking.integration.inventory.release.missing_slot', booking_id=booking_id, hold_reference=hold_reference)
            return

        new_quantity = int(slot.get('quantity_available', 0)) + 1
        await self._update_slot(hold_reference, new_quantity, None)
        logger.info('booking.integration.inventory.release.response', booking_id=booking_id, hold_reference=hold_reference, new_quantity=new_quantity, reason=reason)
