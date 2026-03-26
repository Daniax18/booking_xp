from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest

from adapters.outbound.inventory_client import HttpInventoryClient
from adapters.outbound.payment_client import HttpPaymentClient
from domain.models.booking import ResourceType


@pytest.mark.asyncio
async def test_inventory_client_uses_prepared_contract():
    """Ensure the inventory client sends the expected REST contract payload."""
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured['path'] = request.url.path
        captured['method'] = request.method
        captured['body'] = request.content.decode()
        return httpx.Response(200, json={'available': True})

    client = HttpInventoryClient(
        base_url='http://inventory-service:8002',
        integration_mode='http',
        transport=httpx.MockTransport(handler),
    )
    start_time = datetime.now(timezone.utc) + timedelta(days=4)
    end_time = start_time + timedelta(hours=2)

    result = await client.check_availability(
        resource_id='resource-9',
        resource_type=ResourceType.RESTAURANT_TABLE,
        start_time=start_time,
        end_time=end_time,
        party_size=4,
    )

    assert result.available is True
    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/v1/inventory/internal/availability/check'
    assert 'resource-9' in captured['body']
    assert 'RESTAURANT_TABLE' in captured['body']


@pytest.mark.asyncio
async def test_payment_client_uses_prepared_contract():
    """Ensure the payment client sends the expected REST contract payload."""
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured['path'] = request.url.path
        captured['method'] = request.method
        captured['body'] = request.content.decode()
        return httpx.Response(200, json={'status': 'PAID', 'payment_reference': 'pay-555'})

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
    assert captured['method'] == 'POST'
    assert captured['path'] == '/api/v1/payments/internal/transactions'
    assert 'booking-1' in captured['body']
    assert '120.00' in captured['body']
