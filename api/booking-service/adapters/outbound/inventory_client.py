from datetime import datetime
from uuid import uuid4

import httpx
import structlog

from domain.models.booking import ResourceType
from domain.ports.outbound import InventoryAvailability, InventoryPort, InventoryReservation
from infrastructure.middleware import CORRELATION_ID_HEADER, get_correlation_id


logger = structlog.get_logger(__name__)


class HttpInventoryClient(InventoryPort):
    """Call inventory-service in HTTP mode or simulate it in stub mode."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0, integration_mode: str = 'stub', transport=None):
        self._base_url = base_url.rstrip('/')
        self._timeout_seconds = timeout_seconds
        self._integration_mode = integration_mode.lower()
        self._transport = transport

    def _headers(self) -> dict:
        correlation_id = get_correlation_id()
        return {CORRELATION_ID_HEADER: correlation_id} if correlation_id else {}

    async def check_availability(self, *, resource_id: str, resource_type: ResourceType, start_time: datetime, end_time: datetime, party_size: int) -> InventoryAvailability:
        """Check resource availability through the inventory boundary."""
        if self._integration_mode == 'stub':
            logger.info('booking.integration.inventory.check.stub', resource_id=resource_id, resource_type=resource_type.value)
            return InventoryAvailability(available=True)

        payload = {
            'resource_id': resource_id,
            'resource_type': resource_type.value,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'party_size': party_size,
        }
        logger.info('booking.integration.inventory.check.request', payload=payload)
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.post(f'{self._base_url}/api/v1/inventory/internal/availability/check', json=payload)
            response.raise_for_status()
            body = response.json()
            logger.info('booking.integration.inventory.check.response', status_code=response.status_code, body=body)
            return InventoryAvailability(available=body['available'], reason=body.get('reason'))

    async def reserve(self, *, booking_id: str, resource_id: str, resource_type: ResourceType, start_time: datetime, end_time: datetime, party_size: int) -> InventoryReservation:
        """Request a temporary inventory hold for the booking."""
        if self._integration_mode == 'stub':
            hold_reference = f'inv-{uuid4()}'
            logger.info('booking.integration.inventory.reserve.stub', booking_id=booking_id, hold_reference=hold_reference)
            return InventoryReservation(success=True, hold_reference=hold_reference)

        payload = {
            'booking_id': booking_id,
            'resource_id': resource_id,
            'resource_type': resource_type.value,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'party_size': party_size,
        }
        logger.info('booking.integration.inventory.reserve.request', payload=payload)
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.post(f'{self._base_url}/api/v1/inventory/internal/reservations/hold', json=payload)
            response.raise_for_status()
            body = response.json()
            logger.info('booking.integration.inventory.reserve.response', status_code=response.status_code, body=body)
            return InventoryReservation(success=body['success'], hold_reference=body.get('hold_reference'), reason=body.get('reason'))

    async def release(self, *, booking_id: str, resource_id: str, hold_reference: str | None, reason: str) -> None:
        """Release an existing inventory hold as part of compensation."""
        if self._integration_mode == 'stub':
            logger.info('booking.integration.inventory.release.stub', booking_id=booking_id, hold_reference=hold_reference, reason=reason)
            return

        payload = {
            'booking_id': booking_id,
            'resource_id': resource_id,
            'hold_reference': hold_reference,
            'reason': reason,
        }
        logger.info('booking.integration.inventory.release.request', payload=payload)
        async with httpx.AsyncClient(timeout=self._timeout_seconds, transport=self._transport, headers=self._headers()) as client:
            response = await client.post(f'{self._base_url}/api/v1/inventory/internal/reservations/release', json=payload)
            response.raise_for_status()
