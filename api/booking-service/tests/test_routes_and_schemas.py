from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest
from fastapi import HTTPException

from adapters.inbound.routes import (
    cancel_booking,
    communication_contracts,
    consume_inventory_event,
    consume_payment_event,
    create_booking,
    get_booking,
    health_check,
    list_bookings,
)
from adapters.inbound.schemas import (
    BookingResponse,
    CancelBookingRequest,
    CreateBookingRequest,
    InventoryEventRequest,
    PaymentEventRequest,
)
from adapters.outbound.inventory_client import HttpInventoryClient
from adapters.outbound.payment_client import HttpPaymentClient
from domain.models.booking import Booking, BookingStatus, PaymentStatus, ResourceType, SagaStatus


def _sample_booking(**overrides) -> Booking:
    """Create a representative booking aggregate for API and schema tests."""
    start_time = datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc)
    values = {
        'id': 'booking-123',
        'user_id': 'user-123',
        'resource_id': 'resource-123',
        'resource_type': ResourceType.HOTEL_ROOM,
        'start_time': start_time,
        'end_time': start_time + timedelta(hours=2),
        'party_size': 2,
        'total_price': Decimal('180.00'),
        'status': BookingStatus.CONFIRMED,
        'payment_status': PaymentStatus.PAID,
        'saga_status': SagaStatus.COMPLETED,
        'inventory_hold_reference': 'slot-123',
        'payment_reference': 'payment-123',
        'notes': 'note',
    }
    values.update(overrides)
    return Booking(**values)


class FakeBookingService:
    """Provide deterministic route behavior without touching the database layer."""

    def __init__(self, booking: Booking | None = None):
        self.booking = booking or _sample_booking()
        self.created_payload = None
        self.cancel_payload = None
        self.payment_event_payload = None
        self.inventory_event_payload = None

    async def create_booking(self, **payload):
        self.created_payload = payload
        return self.booking

    async def list_bookings_for_user(self, user_id: str):
        return [self.booking] if user_id == self.booking.user_id else []

    async def handle_payment_event(self, **payload):
        self.payment_event_payload = payload
        return self.booking

    async def handle_inventory_event(self, **payload):
        self.inventory_event_payload = payload
        return self.booking

    async def cancel_booking(self, *, booking_id: str, reason: str):
        self.cancel_payload = {'booking_id': booking_id, 'reason': reason}
        return self.booking

    async def get_booking(self, booking_id: str):
        return self.booking if booking_id == self.booking.id else None


@pytest.mark.asyncio
async def test_health_check_reports_healthy_status():
    """Health route should report healthy when the database query succeeds."""

    class FakeDb:
        async def execute(self, _query):
            return 1

    response = await health_check(db=FakeDb())

    assert response.status == 'healthy'
    assert response.service == 'booking-service'
    assert response.integrations['inventory'] in {'stub', 'http'}


@pytest.mark.asyncio
async def test_health_check_reports_degraded_status_on_database_error():
    """Health route should degrade gracefully when the database is unavailable."""

    class FakeDb:
        async def execute(self, _query):
            raise RuntimeError('database unavailable')

    response = await health_check(db=FakeDb())

    assert response.status == 'degraded'


@pytest.mark.asyncio
async def test_communication_contracts_exposes_real_service_routes():
    """Contracts route should document the integration points used by booking-service."""
    response = await communication_contracts()

    assert response.inventory_rest['get_resource']['path'] == '/api/v1/inventory/resources/{resource_id}'
    assert response.payment_rest['process_payment']['path'] == '/api/v1/payments/{payment_id}/process'
    assert any(event['name'] == 'booking.confirmed' for event in response.published_events)


@pytest.mark.asyncio
async def test_create_booking_route_returns_booking_response(monkeypatch):
    """Create route should transform the service result into the public schema."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)
    payload = CreateBookingRequest(
        user_id='user-123',
        resource_id='resource-123',
        resource_type=ResourceType.HOTEL_ROOM,
        start_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 2, 20, 0, tzinfo=timezone.utc),
        party_size=2,
        quoted_price=Decimal('180.00'),
        notes='note',
    )

    response = await create_booking(payload=payload, db=object())

    assert isinstance(response, BookingResponse)
    assert fake_service.created_payload['resource_id'] == 'resource-123'
    assert response.status == BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_list_bookings_route_returns_domain_objects_as_schema(monkeypatch):
    """List route should map all returned bookings to response models."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)

    response = await list_bookings(user_id='user-123', db=object())

    assert len(response) == 1
    assert response[0].id == 'booking-123'


@pytest.mark.asyncio
async def test_payment_event_route_returns_booking(monkeypatch):
    """Payment event route should delegate to the booking service."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)
    payload = PaymentEventRequest(booking_id='booking-123', status='PAID', payment_reference='payment-123')

    response = await consume_payment_event(payload=payload, db=object())

    assert response.payment_reference == 'payment-123'
    assert fake_service.payment_event_payload['status'] == 'PAID'


@pytest.mark.asyncio
async def test_inventory_event_route_returns_booking(monkeypatch):
    """Inventory event route should delegate to the booking service."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)
    payload = InventoryEventRequest(booking_id='booking-123', status='RELEASED', hold_reference='slot-123')

    response = await consume_inventory_event(payload=payload, db=object())

    assert response.inventory_hold_reference == 'slot-123'
    assert fake_service.inventory_event_payload['hold_reference'] == 'slot-123'


@pytest.mark.asyncio
async def test_cancel_booking_route_returns_booking(monkeypatch):
    """Cancel route should call the service with the route parameter and body reason."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)

    response = await cancel_booking(
        booking_id='booking-123',
        payload=CancelBookingRequest(reason='user_requested'),
        db=object(),
    )

    assert response.id == 'booking-123'
    assert fake_service.cancel_payload == {'booking_id': 'booking-123', 'reason': 'user_requested'}


@pytest.mark.asyncio
async def test_get_booking_route_returns_booking(monkeypatch):
    """Get route should return the mapped response when the booking exists."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)

    response = await get_booking(booking_id='booking-123', db=object())

    assert response.id == 'booking-123'


@pytest.mark.asyncio
async def test_get_booking_route_raises_not_found(monkeypatch):
    """Get route should return an HTTP 404 when the booking does not exist."""
    fake_service = FakeBookingService()
    monkeypatch.setattr('adapters.inbound.routes.get_booking_service', lambda _db: fake_service)

    with pytest.raises(HTTPException) as exc_info:
        await get_booking(booking_id='missing-booking', db=object())

    assert exc_info.value.status_code == 404


def test_create_booking_request_and_response_models_validate_data():
    """Pydantic schemas should preserve business values and serialize domain objects."""
    payload = CreateBookingRequest(
        user_id='user-123',
        resource_id='resource-123',
        resource_type='VENUE',
        start_time='2026-04-02T18:00:00Z',
        end_time='2026-04-02T22:00:00Z',
        party_size=40,
        quoted_price='250.00',
        notes='soiree privee',
    )
    booking = _sample_booking(resource_type=ResourceType.VENUE, party_size=40, total_price=Decimal('250.00'))
    response = BookingResponse.from_domain(booking)

    assert payload.resource_type == ResourceType.VENUE
    assert payload.quoted_price == Decimal('250.00')
    assert response.resource_type == ResourceType.VENUE
    assert response.total_price == Decimal('250.00')


def test_cancel_request_uses_default_reason():
    """Cancellation schema should provide the default business reason."""
    payload = CancelBookingRequest()
    assert payload.reason == 'cancelled_by_user'


@pytest.mark.asyncio
async def test_inventory_client_handles_inactive_capacity_and_exhausted_slots():
    """Inventory client should report detailed unavailability reasons from public routes."""
    scenarios = [
        (
            {'id': 'resource-1', 'capacity': 4, 'is_active': False},
            [],
            'resource_inactive',
        ),
        (
            {'id': 'resource-1', 'capacity': 2, 'is_active': True},
            [],
            'party_size_exceeds_capacity',
        ),
        (
            {'id': 'resource-1', 'capacity': 4, 'is_active': True},
            [],
            'no_matching_slot',
        ),
        (
            {'id': 'resource-1', 'capacity': 4, 'is_active': True},
            [{
                'id': 'slot-1',
                'start_time': '2026-04-02T17:00:00+00:00',
                'end_time': '2026-04-02T23:00:00+00:00',
                'is_available': False,
                'quantity_available': 1,
                'reason_if_unavailable': 'maintenance',
            }],
            'maintenance',
        ),
        (
            {'id': 'resource-1', 'capacity': 4, 'is_active': True},
            [{
                'id': 'slot-1',
                'start_time': '2026-04-02T17:00:00+00:00',
                'end_time': '2026-04-02T23:00:00+00:00',
                'is_available': True,
                'quantity_available': 0,
                'reason_if_unavailable': None,
            }],
            'slot_exhausted',
        ),
    ]

    for resource_payload, slots_payload, expected_reason in scenarios:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith('/resources/resource-1'):
                return httpx.Response(200, json=resource_payload)
            if request.url.path.endswith('/availability/resource-1'):
                return httpx.Response(200, json=slots_payload)
            raise AssertionError(f'Unexpected request {request.method} {request.url.path}')

        client = HttpInventoryClient(
            base_url='http://inventory-service:8002',
            integration_mode='http',
            transport=httpx.MockTransport(handler),
        )
        result = await client.check_availability(
            resource_id='resource-1',
            resource_type=ResourceType.HOTEL_ROOM,
            start_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 4, 2, 20, 0, tzinfo=timezone.utc),
            party_size=4,
        )

        assert result.available is False
        assert result.reason == expected_reason


@pytest.mark.asyncio
async def test_inventory_client_reserve_and_release_cover_real_branches():
    """Inventory client should reserve, reject, and release slots using real inventory routes."""
    state = {
        'slots': [{
            'id': 'slot-1',
            'resource_id': 'resource-1',
            'start_time': '2026-04-02T17:00:00+00:00',
            'end_time': '2026-04-02T23:00:00+00:00',
            'is_available': True,
            'quantity_available': 1,
            'reason_if_unavailable': None,
        }],
        'updates': [],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path.endswith('/availability/resource-1'):
            return httpx.Response(200, json=state['slots'])
        if request.method == 'PUT' and request.url.path.endswith('/availability/slot-1'):
            body = __import__('json').loads(request.content.decode())
            state['updates'].append(body)
            state['slots'][0]['quantity_available'] = body['quantity']
            state['slots'][0]['reason_if_unavailable'] = body['reason_if_unavailable']
            state['slots'][0]['is_available'] = body['quantity'] > 0
            return httpx.Response(200, json=state['slots'][0])
        raise AssertionError(f'Unexpected request {request.method} {request.url.path}')

    client = HttpInventoryClient(
        base_url='http://inventory-service:8002',
        integration_mode='http',
        transport=httpx.MockTransport(handler),
    )

    reserved = await client.reserve(
        booking_id='booking-123',
        resource_id='resource-1',
        resource_type=ResourceType.HOTEL_ROOM,
        start_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 2, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
    await client.release(
        booking_id='booking-123',
        resource_id='resource-1',
        hold_reference='slot-1',
        reason='compensation',
    )

    state['slots'][0]['is_available'] = False
    state['slots'][0]['quantity_available'] = 0
    unavailable = await client.reserve(
        booking_id='booking-123',
        resource_id='resource-1',
        resource_type=ResourceType.HOTEL_ROOM,
        start_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 2, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )

    assert reserved.success is True
    assert reserved.hold_reference == 'slot-1'
    assert state['updates'][0]['quantity'] == 0
    assert state['updates'][1]['quantity'] == 1
    assert unavailable.success is False
    assert unavailable.reason == 'slot_unavailable'


@pytest.mark.asyncio
async def test_inventory_client_stub_and_missing_hold_reference_are_safe():
    """Inventory client should support stub mode and tolerate missing hold references."""
    client = HttpInventoryClient(base_url='http://inventory-service:8002', integration_mode='stub')

    availability = await client.check_availability(
        resource_id='resource-1',
        resource_type=ResourceType.HOTEL_ROOM,
        start_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 2, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
    reservation = await client.reserve(
        booking_id='booking-123',
        resource_id='resource-1',
        resource_type=ResourceType.HOTEL_ROOM,
        start_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 4, 2, 20, 0, tzinfo=timezone.utc),
        party_size=2,
    )
    await client.release(
        booking_id='booking-123',
        resource_id='resource-1',
        hold_reference=None,
        reason='noop',
    )

    assert availability.available is True
    assert reservation.success is True
    assert reservation.hold_reference == 'inv-booking-123'


@pytest.mark.asyncio
async def test_payment_client_cancel_payment_covers_paid_pending_and_stub_paths():
    """Payment client should refund paid payments, cancel pending ones, and ignore missing references."""
    state = {'calls': []}

    async def handler(request: httpx.Request) -> httpx.Response:
        state['calls'].append((request.method, request.url.path))
        if request.method == 'GET' and request.url.path.endswith('/payments/payment-paid'):
            return httpx.Response(200, json={'id': 'payment-paid', 'status': 'PAID'})
        if request.method == 'GET' and request.url.path.endswith('/payments/payment-pending'):
            return httpx.Response(200, json={'id': 'payment-pending', 'status': 'PENDING'})
        if request.method == 'GET' and request.url.path.endswith('/payments/payment-refunded'):
            return httpx.Response(200, json={'id': 'payment-refunded', 'status': 'REFUNDED'})
        if request.method == 'POST' and request.url.path.endswith('/payments/payment-paid/refund'):
            return httpx.Response(200, json={'id': 'payment-paid', 'status': 'REFUNDED'})
        if request.method == 'POST' and request.url.path.endswith('/payments/payment-pending/cancel'):
            return httpx.Response(200, json={'id': 'payment-pending', 'status': 'CANCELLED'})
        raise AssertionError(f'Unexpected request {request.method} {request.url.path}')

    client = HttpPaymentClient(
        base_url='http://payment-service:8004',
        integration_mode='http',
        transport=httpx.MockTransport(handler),
    )

    await client.cancel_payment(booking_id='booking-123', payment_reference='payment-paid', reason='refund')
    await client.cancel_payment(booking_id='booking-123', payment_reference='payment-pending', reason='cancel')
    await client.cancel_payment(booking_id='booking-123', payment_reference='payment-refunded', reason='noop')
    await client.cancel_payment(booking_id='booking-123', payment_reference=None, reason='missing')
    await HttpPaymentClient(base_url='http://payment-service:8004', integration_mode='stub').cancel_payment(
        booking_id='booking-123',
        payment_reference='payment-stub',
        reason='stub',
    )

    assert ('POST', '/api/v1/payments/payment-paid/refund') in state['calls']
    assert ('POST', '/api/v1/payments/payment-pending/cancel') in state['calls']
    assert ('GET', '/api/v1/payments/payment-refunded') in state['calls']


@pytest.mark.asyncio
async def test_payment_client_propagates_reason_from_processed_payment():
    """Payment initiation should surface a payment-service error message when present."""

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'POST' and request.url.path == '/api/v1/payments/':
            return httpx.Response(201, json={'id': 'payment-1', 'status': 'PENDING'})
        if request.method == 'POST' and request.url.path == '/api/v1/payments/payment-1/process':
            return httpx.Response(200, json={'id': 'payment-1', 'status': 'FAILED', 'error_message': 'card_declined'})
        raise AssertionError(f'Unexpected request {request.method} {request.url.path}')

    client = HttpPaymentClient(
        base_url='http://payment-service:8004',
        integration_mode='http',
        transport=httpx.MockTransport(handler),
    )

    result = await client.initiate_payment(
        booking_id='booking-123',
        user_id='user-123',
        amount=Decimal('180.00'),
        currency='EUR',
        resource_type=ResourceType.HOTEL_ROOM,
    )

    assert result.status == 'FAILED'
    assert result.reason == 'card_declined'
