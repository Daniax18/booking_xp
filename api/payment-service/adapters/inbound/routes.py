"""
Routes API — Adaptateur Inbound FastAPI

📚 Explication Pédagogique :
Les routes HTTP sont des ADAPTATEURS INBOUND.
Elles reçoivent les requêtes HTTP et appellent le domaine (PaymentService).

Flux complet :
1. FastAPI reçoit la requête HTTP
2. Pydantic valide le payload JSON
3. La route appelle le PaymentService via le port inbound
4. Le service exécute la logique métier (avec décorateurs optionnels)
5. La réponse remonte avec le schéma de sortie
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.schemas import (
    CreatePaymentRequest, RefundPaymentRequest,
    PaymentResponse, PaymentListResponse,
    HealthResponse, MessageResponse,
)
from adapters.outbound.repositories import PostgresPaymentRepository
from adapters.outbound.event_publisher import InMemoryEventPublisher
from adapters.outbound.payment_provider import MockPaymentProvider
from adapters.outbound.log_service_client import HttpLogServiceClient
from adapters.outbound.audit_service_client import HttpAuditServiceClient
from domain.models.payment import PaymentStatus, PaymentMethod
from domain.services.payment_service import PaymentService
from domain.services.payment_decorators import (
    PaymentLoggingDecorator, PaymentValidationDecorator, PaymentMetricsDecorator,
)
from infrastructure.config import get_settings
from infrastructure.database import get_db_session


router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


def _to_payment_response(payment) -> PaymentResponse:
    """Convertir une entité Payment en réponse HTTP."""
    return PaymentResponse(
        id=payment.id,
        booking_id=payment.booking_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status.value,
        method=payment.method.value,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        refunded_amount=payment.refunded_amount,
        refund_percentage=payment.refund_percentage(),
        metadata=payment.metadata,
        error_message=payment.error_message,
    )


def get_payment_service(db: AsyncSession) -> PaymentService:
    """
    Factory pour créer le PaymentService avec :
    - Ports outbound concrets
    - Décorateurs appliqués
    """
    settings = get_settings()
    
    # Ports outbound
    repository = PostgresPaymentRepository(db)
    event_publisher = InMemoryEventPublisher()
    payment_provider = MockPaymentProvider()
    system_log_port = HttpLogServiceClient(
        base_url=settings.LOG_SERVICE_URL,
        timeout_seconds=settings.LOG_SERVICE_TIMEOUT_SECONDS,
    )
    audit_log_port = HttpAuditServiceClient(
        base_url=settings.LOG_SERVICE_URL,
        timeout_seconds=settings.LOG_SERVICE_TIMEOUT_SECONDS,
    )
    
    # Service métier
    service = PaymentService(
        repository=repository,
        event_publisher=event_publisher,
        payment_provider=payment_provider,
        system_log_port=system_log_port,
        audit_log_port=audit_log_port,
    )
    
    # Appliquer les décorateurs
    service = PaymentLoggingDecorator(service)
    service = PaymentValidationDecorator(service)
    service = PaymentMetricsDecorator(service)
    
    return service


# ────────────────── ENDPOINTS ──────────────────

# NOTE: The health endpoint must be defined BEFORE the "/{payment_id}" route
# to avoid being matched as a payment lookup (FastAPI matches routes in order)

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Vérifier la santé du service",
)
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Vérifier que le service et la DB sont opérationnels."""
    try:
        await db.execute(text("SELECT 1"))
        status_value = "healthy"
    except Exception:
        status_value = "degraded"
    
    return HealthResponse(status=status_value)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un paiement",
)
async def create_payment(
    request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Créer un nouveau paiement pour une réservation."""
    service = get_payment_service(db)
    
    try:
        payment = await service.create_payment(
            booking_id=request.booking_id,
            amount=request.amount,
            currency=request.currency,
            method=PaymentMethod(request.method),
            metadata=request.metadata,
        )
        return _to_payment_response(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Récupérer un paiement",
)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Récupérer les détails d'un paiement."""
    service = get_payment_service(db)
    payment = await service.get_payment(payment_id)
    
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    return _to_payment_response(payment)


@router.get(
    "/booking/{booking_id}",
    response_model=PaymentListResponse,
    summary="Lister les paiements d'une réservation",
)
async def get_payments_by_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Récupérer tous les paiements associés à une réservation."""
    service = get_payment_service(db)
    payments = await service.get_payments_by_booking(booking_id)
    
    return PaymentListResponse(
        items=[_to_payment_response(p) for p in payments],
        total=len(payments),
        limit=len(payments),
        offset=0,
    )


@router.post(
    "/{payment_id}/process",
    response_model=PaymentResponse,
    summary="Traiter un paiement",
    description="Envoyer le paiement au provider pour validation.",
)
async def process_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Traiter un paiement auprès du provider (Stripe, PayPal, etc.)."""
    service = get_payment_service(db)
    
    try:
        payment = await service.process_payment(payment_id)
        return _to_payment_response(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{payment_id}/confirm",
    response_model=PaymentResponse,
    summary="Confirmer manuellement un paiement",
)
async def confirm_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Confirmer manuellement qu'un paiement est validé (fallback)."""
    service = get_payment_service(db)
    
    try:
        payment = await service.confirm_payment(payment_id)
        return _to_payment_response(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentResponse,
    summary="Annuler un paiement",
)
async def cancel_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Annuler un paiement en attente."""
    service = get_payment_service(db)
    
    try:
        payment = await service.cancel_payment(payment_id)
        return _to_payment_response(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{payment_id}/refund",
    response_model=PaymentResponse,
    summary="Rembourser un paiement",
)
async def refund_payment(
    payment_id: str,
    request: RefundPaymentRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Rembourser un paiement (partiellement ou totalement)."""
    service = get_payment_service(db)
    
    try:
        payment = await service.refund_payment(payment_id, request.refund_amount)
        return _to_payment_response(payment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/",
    response_model=PaymentListResponse,
    summary="Lister les paiements",
)
async def list_payments(
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    """Lister les paiements avec filtres optionnels."""
    service = get_payment_service(db)
    
    try:
        payment_status = PaymentStatus(status) if status else None
        payments = await service.list_payments(payment_status, limit, offset)
        
        return PaymentListResponse(
            items=[_to_payment_response(p) for p in payments],
            total=len(payments),
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# End of routes
