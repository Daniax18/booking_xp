"""
Pydantic Schemas — Validação et (dé)sérialisation HTTP

📚 Explication Pédagogique :
Les schémas définissent le contrat de l'API.
Ils valident les données entrantes et sérialisent les réponses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ────────────────── Requêtes Entrantes ──────────────────

class CreatePaymentRequest(BaseModel):
    """Payload pour créer un paiement."""
    booking_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    method: str = Field(default="CREDIT_CARD")
    metadata: Optional[dict] = Field(default=None)


class RefundPaymentRequest(BaseModel):
    """Payload pour rembourser un paiement."""
    refund_amount: Optional[float] = Field(None, gt=0)


# ────────────────── Réponses Sortantes ──────────────────

class PaymentResponse(BaseModel):
    """Modèle de réponse pour un paiement."""
    id: str
    booking_id: str
    amount: float
    currency: str
    status: str
    method: str
    created_at: datetime
    updated_at: datetime
    refunded_amount: float
    refund_percentage: float
    metadata: dict
    error_message: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "pay-123",
                "booking_id": "book-456",
                "amount": 100.0,
                "currency": "EUR",
                "status": "PAID",
                "method": "CREDIT_CARD",
                "created_at": "2026-03-25T10:00:00",
                "updated_at": "2026-03-25T10:05:00",
                "refunded_amount": 0.0,
                "refund_percentage": 0.0,
                "metadata": {},
                "error_message": None,
            }
        }


class PaymentListResponse(BaseModel):
    """Liste de paiements avec pagination."""
    items: list[PaymentResponse]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    """Réponse du health check."""
    status: str
    service: str = "payment-service"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageResponse(BaseModel):
    """Réponse générique avec message."""
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
