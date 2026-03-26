from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.schemas import (
    BookingResponse,
    CancelBookingRequest,
    CommunicationContractsResponse,
    CreateBookingRequest,
    HealthResponse,
    InventoryEventRequest,
    PaymentEventRequest,
)
from adapters.outbound.event_publisher import StructlogEventPublisher
from adapters.outbound.inventory_client import HttpInventoryClient
from adapters.outbound.log_service_client import HttpLogServiceClient
from adapters.outbound.payment_client import HttpPaymentClient
from adapters.outbound.repositories import PostgresBookingRepository
from domain.pricing import PricingStrategyFactory
from domain.services.booking_service import BookingConflictError, BookingError, BookingNotFoundError, BookingService
from infrastructure.config import get_settings
from infrastructure.database import get_db_session


router = APIRouter(prefix='/api/v1/bookings', tags=['Bookings'])


def _build_log_client() -> HttpLogServiceClient:
    """Create a concrete log-service client from runtime settings."""
    settings = get_settings()
    return HttpLogServiceClient(
        base_url=settings.LOG_SERVICE_URL,
        service_name=settings.SERVICE_NAME,
        timeout_seconds=settings.LOG_SERVICE_TIMEOUT_SECONDS,
    )


def get_booking_service(db: AsyncSession) -> BookingService:
    """Assemble the booking application service and all outbound adapters."""
    settings = get_settings()
    log_client = _build_log_client()
    return BookingService(
        booking_repository=PostgresBookingRepository(db),
        inventory_port=HttpInventoryClient(
            base_url=settings.INVENTORY_SERVICE_URL,
            timeout_seconds=settings.INVENTORY_SERVICE_TIMEOUT_SECONDS,
            integration_mode=settings.INVENTORY_INTEGRATION_MODE,
        ),
        payment_port=HttpPaymentClient(
            base_url=settings.PAYMENT_SERVICE_URL,
            timeout_seconds=settings.PAYMENT_SERVICE_TIMEOUT_SECONDS,
            integration_mode=settings.PAYMENT_INTEGRATION_MODE,
        ),
        audit_log_port=log_client,
        system_log_port=log_client,
        event_publisher=StructlogEventPublisher(system_log_port=log_client),
        pricing_strategy_factory=PricingStrategyFactory(),
    )


@router.get('/health', response_model=HealthResponse, tags=['Health'])
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Check API, database, and integration configuration health."""
    settings = get_settings()
    try:
        await db.execute(text('SELECT 1'))
        status_value = 'healthy'
    except Exception:
        status_value = 'degraded'
    return HealthResponse(
        status=status_value,
        service=settings.SERVICE_NAME,
        integrations={
            'inventory': settings.INVENTORY_INTEGRATION_MODE,
            'payment': settings.PAYMENT_INTEGRATION_MODE,
            'logging': 'http',
        },
    )


@router.get('/contracts/communication', response_model=CommunicationContractsResponse, tags=['Contracts'])
async def communication_contracts():
    """Expose the prepared REST and event contracts for inter-service integration."""
    return CommunicationContractsResponse(
        inventory_rest={
            'get_resource': {
                'method': 'GET',
                'path': '/api/v1/inventory/resources/{resource_id}',
            },
            'get_availability': {
                'method': 'GET',
                'path': '/api/v1/inventory/availability/{resource_id}',
            },
            'reserve_slot': {
                'method': 'PUT',
                'path': '/api/v1/inventory/availability/{slot_id}',
                'payload': {
                    'quantity': 0,
                    'reason_if_unavailable': 'reserved_by_booking_service',
                },
            },
            'release_slot': {
                'method': 'PUT',
                'path': '/api/v1/inventory/availability/{slot_id}',
                'payload': {
                    'quantity': 1,
                    'reason_if_unavailable': None,
                },
            },
        },
        payment_rest={
            'create_payment': {
                'method': 'POST',
                'path': '/api/v1/payments/',
                'payload': {
                    'booking_id': 'uuid',
                    'amount': 149.99,
                    'currency': 'EUR',
                    'method': 'CREDIT_CARD',
                    'metadata': {
                        'user_id': 'uuid',
                        'resource_type': 'HOTEL_ROOM|RESTAURANT_TABLE|VENUE',
                    },
                },
            },
            'process_payment': {
                'method': 'POST',
                'path': '/api/v1/payments/{payment_id}/process',
            },
            'cancel_or_refund_payment': {
                'method': 'POST',
                'path': '/api/v1/payments/{payment_id}/cancel or /refund',
            },
        },
        published_events=[
            {'name': 'booking.created', 'payload': {'booking_id': 'uuid', 'status': 'PENDING'}},
            {'name': 'booking.confirmed', 'payload': {'booking_id': 'uuid', 'status': 'CONFIRMED'}},
            {'name': 'booking.cancelled', 'payload': {'booking_id': 'uuid', 'status': 'CANCELLED'}},
            {'name': 'booking.payment_failed', 'payload': {'booking_id': 'uuid', 'payment_status': 'FAILED'}},
        ],
        consumed_events=[
            {'name': 'payment.status_changed', 'path': '/api/v1/bookings/events/payment'},
            {'name': 'inventory.status_changed', 'path': '/api/v1/bookings/events/inventory'},
        ],
    )


@router.post('', response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(payload: CreateBookingRequest, db: AsyncSession = Depends(get_db_session)):
    """Create a booking and launch the booking plus payment saga."""
    service = get_booking_service(db)
    try:
        booking = await service.create_booking(**payload.model_dump())
    except BookingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BookingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BookingResponse.from_domain(booking)


@router.get('', response_model=list[BookingResponse])
async def list_bookings(user_id: str, db: AsyncSession = Depends(get_db_session)):
    """Return all bookings created by one user."""
    service = get_booking_service(db)
    bookings = await service.list_bookings_for_user(user_id)
    return [BookingResponse.from_domain(booking) for booking in bookings]


@router.post('/events/payment', response_model=BookingResponse)
async def consume_payment_event(payload: PaymentEventRequest, db: AsyncSession = Depends(get_db_session)):
    """Consume a payment callback or asynchronous event."""
    service = get_booking_service(db)
    try:
        booking = await service.handle_payment_event(**payload.model_dump())
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BookingResponse.from_domain(booking)


@router.post('/events/inventory', response_model=BookingResponse)
async def consume_inventory_event(payload: InventoryEventRequest, db: AsyncSession = Depends(get_db_session)):
    """Consume an inventory callback or asynchronous event."""
    service = get_booking_service(db)
    try:
        booking = await service.handle_inventory_event(**payload.model_dump())
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BookingResponse.from_domain(booking)


@router.post('/{booking_id}/cancel', response_model=BookingResponse)
async def cancel_booking(booking_id: str, payload: CancelBookingRequest, db: AsyncSession = Depends(get_db_session)):
    """Cancel a booking and trigger the compensation flow."""
    service = get_booking_service(db)
    try:
        booking = await service.cancel_booking(booking_id=booking_id, reason=payload.reason)
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BookingResponse.from_domain(booking)


@router.get('/{booking_id}', response_model=BookingResponse)
async def get_booking(booking_id: str, db: AsyncSession = Depends(get_db_session)):
    """Return one booking by identifier."""
    service = get_booking_service(db)
    booking = await service.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Booking not found')
    return BookingResponse.from_domain(booking)

