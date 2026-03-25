"""
DECORATOR PATTERN — Décorateurs pour enrichir le service

📚 Explication Pédagogique :
Les décorateurs permettent d'ajouter des responsabilités à une classe
SANS modifier la classe elle-même.

Exemple de décorateurs :
1. PaymentLoggingDecorator : log en détail chaque opération
2. PaymentValidationDecorator : ajoute des validations supplémentaires
3. PaymentCachingDecorator : cache les résultats
4. PaymentMetricsDecorator : collecte des métriques

Le décorateur wraps le service et délègue l'appel au service réel,
tout en ajoutant de la logique supplémentaire.

Avantage : Respect du Single Responsibility Principle
Logging, validation, cache ne sont pas dans le service métier.
"""
from typing import Optional
import structlog
from datetime import datetime

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from domain.ports.inbound import PaymentInputPort
from domain.models.payment_event import PaymentEvent


logger = structlog.get_logger(__name__)


class PaymentServiceDecorator(PaymentInputPort):
    """Classe de base pour les décorateurs."""
    
    def __init__(self, service: PaymentInputPort):
        """Wrapping du service réel."""
        self._service = service
    
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        currency: str = "EUR",
        method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        metadata: Optional[dict] = None,
    ) -> Payment:
        """Déléguer au service réel."""
        return await self._service.create_payment(
            booking_id, amount, currency, method, metadata
        )
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Déléguer au service réel."""
        return await self._service.get_payment(payment_id)
    
    async def get_payments_by_booking(self, booking_id: str) -> list[Payment]:
        """Déléguer au service réel."""
        return await self._service.get_payments_by_booking(booking_id)
    
    async def process_payment(self, payment_id: str) -> Payment:
        """Déléguer au service réel."""
        return await self._service.process_payment(payment_id)
    
    async def confirm_payment(self, payment_id: str) -> Payment:
        """Déléguer au service réel."""
        return await self._service.confirm_payment(payment_id)
    
    async def cancel_payment(self, payment_id: str) -> Payment:
        """Déléguer au service réel."""
        return await self._service.cancel_payment(payment_id)
    
    async def refund_payment(
        self,
        payment_id: str,
        refund_amount: Optional[float] = None,
    ) -> Payment:
        """Déléguer au service réel."""
        return await self._service.refund_payment(payment_id, refund_amount)
    
    async def list_payments(
        self,
        status: Optional[PaymentStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """Déléguer au service réel."""
        return await self._service.list_payments(status, limit, offset)


class PaymentLoggingDecorator(PaymentServiceDecorator):
    """
    Décorateur 1 : Logging détaillé.
    
    Ajoute des logs structurés pour chaque opération
    sans modifier le service métier.
    """
    
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        currency: str = "EUR",
        method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        metadata: Optional[dict] = None,
    ) -> Payment:
        start_time = datetime.utcnow()
        try:
            payment = await self._service.create_payment(
                booking_id, amount, currency, method, metadata
            )
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "✅ create_payment SUCCESS",
                payment_id=payment.id,
                booking_id=booking_id,
                amount=amount,
                duration_ms=elapsed * 1000,
            )
            return payment
        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "❌ create_payment FAILED",
                booking_id=booking_id,
                error=str(e),
                duration_ms=elapsed * 1000,
            )
            raise
    
    async def process_payment(self, payment_id: str) -> Payment:
        start_time = datetime.utcnow()
        try:
            payment = await self._service.process_payment(payment_id)
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "✅ process_payment SUCCESS",
                payment_id=payment_id,
                status=payment.status.value,
                duration_ms=elapsed * 1000,
            )
            return payment
        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "❌ process_payment FAILED",
                payment_id=payment_id,
                error=str(e),
                duration_ms=elapsed * 1000,
            )
            raise
    
    async def refund_payment(
        self,
        payment_id: str,
        refund_amount: Optional[float] = None,
    ) -> Payment:
        start_time = datetime.utcnow()
        try:
            payment = await self._service.refund_payment(payment_id, refund_amount)
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "✅ refund_payment SUCCESS",
                payment_id=payment_id,
                refund_amount=refund_amount or payment.amount,
                duration_ms=elapsed * 1000,
            )
            return payment
        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "❌ refund_payment FAILED",
                payment_id=payment_id,
                error=str(e),
                duration_ms=elapsed * 1000,
            )
            raise


class PaymentValidationDecorator(PaymentServiceDecorator):
    """
    Décorateur 2 : Validations supplémentaires.
    
    Ajoute des checks métier avant de déléguer au service.
    """
    
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        currency: str = "EUR",
        method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        metadata: Optional[dict] = None,
    ) -> Payment:
        # Validations supplémentaires
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > 1_000_000:
            logger.warning("Large payment detected", amount=amount)
        if not booking_id.strip():
            raise ValueError("booking_id required")
        
        return await self._service.create_payment(
            booking_id, amount, currency, method, metadata
        )
    
    async def refund_payment(
        self,
        payment_id: str,
        refund_amount: Optional[float] = None,
    ) -> Payment:
        if refund_amount is not None and refund_amount <= 0:
            raise ValueError("Refund amount must be positive")
        
        return await self._service.refund_payment(payment_id, refund_amount)


class PaymentMetricsDecorator(PaymentServiceDecorator):
    """
    Décorateur 3 : Collecte de métriques.
    
    Enregistre des statistiques pour monitoring & analytics.
    """
    
    def __init__(self, service: PaymentInputPort):
        super().__init__(service)
        self.metrics = {
            "created_count": 0,
            "processed_count": 0,
            "refunded_count": 0,
            "errors_count": 0,
        }
    
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        currency: str = "EUR",
        method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        metadata: Optional[dict] = None,
    ) -> Payment:
        try:
            payment = await self._service.create_payment(
                booking_id, amount, currency, method, metadata
            )
            self.metrics["created_count"] += 1
            return payment
        except Exception:
            self.metrics["errors_count"] += 1
            raise
    
    async def process_payment(self, payment_id: str) -> Payment:
        try:
            payment = await self._service.process_payment(payment_id)
            self.metrics["processed_count"] += 1
            return payment
        except Exception:
            self.metrics["errors_count"] += 1
            raise
    
    async def refund_payment(
        self,
        payment_id: str,
        refund_amount: Optional[float] = None,
    ) -> Payment:
        try:
            payment = await self._service.refund_payment(payment_id, refund_amount)
            self.metrics["refunded_count"] += 1
            return payment
        except Exception:
            self.metrics["errors_count"] += 1
            raise
    
    def get_metrics(self) -> dict:
        """Récupérer les métriques collectées."""
        return self.metrics.copy()
