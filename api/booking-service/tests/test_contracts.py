from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest

from adapters.outbound.inventory_client import HttpInventoryClient
from adapters.outbound.payment_client import HttpPaymentClient
from domain.models.booking import ResourceType


@pytest.mark.asyncio
async def test_inventory_client_uses_real_inventory_contracts():
    """Ensure the inventory client uses the public routes exposed by inventory-service."""
    calls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, request.content.decode()))
        if request.method == 'GET' and request.url.path == '/api/v1/inventory/resources/resource-9':
            return httpx.Response(200, json={'id': 'resource-9', 'capacity': 4, 'is_active': True})
        if request.method == 'GET' and request.url.path == '/api/v1/inventory/availability/resource-9':
            return httpx.Response(
                200,
                json=[{
                    'id': 'slot-1',
                    'resource_id': 'resource-9',
                    'start_time': '2026-03-30T10:00:00+00:00',
                    'end_time': '2026-03-30T14:00:00+00:00',
                    'is_available': True,
                    'quantity_available': 2,
                    'reason_if_unavailable': None,
                    'duration_minutes': 240,
                    'created_at': '2026-03-20T08:00:00+00:00',
                    'updated_at': '2026-03-20T08:00:00+00:00',
                }],
            )
        raise AssertionError(f'Unexpected inventory request: {request.method} {request.url.path}')

    client = HttpInventoryClient(
        base_url='http://inventory-service:8002',
        integration_mode='http',
        transport=httpx.MockTransport(handler),
    )

    result = await client.check_availability(
        resource_id='resource-9',
        resource_type=ResourceType.RESTAURANT_TABLE,
        start_time=datetime(2026, 3, 30, 11, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc),
        party_size=4,
    )

    assert result.available is True
    assert calls[0][1] == '/api/v1/inventory/resources/resource-9'
    assert calls[1][1] == '/api/v1/inventory/availability/resource-9'


@pytest.mark.asyncio
async def test_payment_client_uses_real_payment_contracts():
    """Ensure the payment client follows create then process against payment-service."""
    calls = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, request.content.decode()))
        if request.method == 'POST' and request.url.path == '/api/v1/payments/':
            return httpx.Response(201, json={'id': 'payment-1', 'status': 'PENDING'})
        if request.method == 'POST' and request.url.path == '/api/v1/payments/payment-1/process':
            return httpx.Response(200, json={'id': 'payment-1', 'status': 'PAID', 'error_message': None})
        raise AssertionError(f'Unexpected payment request: {request.method} {request.url.path}')

    client = HttpPaymentClient(
        base_url='http://payment-service:8004',
        integration_mode='http',
        transport=httpx.MockTransport(handler),
    )

    result = await client.initiate_payment(
        booking_id='booking-1',
        user_id='user-1',
        amount=Decimal('120.00'),
        currency='EUR',
        resource_type=ResourceType.VENUE,
    )

    assert result.status == 'PAID'
    assert result.payment_reference == 'payment-1'
    assert calls[0][1] == '/api/v1/payments/'
    assert 'booking-1' in calls[0][2]
    assert calls[1][1] == '/api/v1/payments/payment-1/process'
