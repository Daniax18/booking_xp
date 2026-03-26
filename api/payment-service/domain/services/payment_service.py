"""
PaymentService — Service métier avec Design Patterns

📚 Design Patterns utilisés :

1. OBSERVER PATTERN :
   - Les PaymentEventPublisher écoutent les changements de paiement
   - Quand un paiement passe à PAID, l'événement PaymentPaidEvent
     est publié et consommé par d'autres services (booking, notification, etc.)

2. DECORATOR PATTERN :
   - PaymentProcessingDecorator : ajoute de la logique (validation, logs)
   - PaymentLoggingDecorator : ajoute la traçabilité sans modifier PaymentService
   - Le décorateur wraps le service et enrichit son comportement

3. EVENT SOURCING / Domain Events :
   - Chaque action émet un événement (PaymentCreatedEvent, PaymentPaidEvent, etc.)
   - Ces événements peuvent être rejoués pour reconstruire l'état
   - Assure la traçabilité complète de chaque paiement
"""
from typing import Optional
import structlog

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from domain.models.payment_event import (
    PaymentEvent, PaymentCreatedEvent, PaymentProcessingStartedEvent,
    PaymentPaidEvent, PaymentFailedEvent, PaymentCancelledEvent,
    PaymentRefundedEvent,
)
from domain.ports.inbound import PaymentInputPort
from domain.ports.outbound import (
    PaymentRepository, PaymentEventPublisher, PaymentProvider,
    SystemLogPort, AuditLogPort,
)


logger = structlog.get_logger(__name__)


class PaymentService(PaymentInputPort):
    """
    Service métier pour la gestion des paiements.
    
    Responsabilités :
    - Orchestrer les use cases de paiement
    - Valider les règles métier
    - Émettre des événements (Observer Pattern)
    - Coordonner les appels aux ports outbound
    """
    
    def __init__(
        self,
        repository: PaymentRepository,
        event_publisher: PaymentEventPublisher,
        payment_provider: PaymentProvider,
        system_log_port: SystemLogPort,
        audit_log_port: AuditLogPort,
    ):
        """Injection de dépendances."""
        self._repository = repository
        self._event_publisher = event_publisher
        self._payment_provider = payment_provider
        self._system_log_port = system_log_port
        self._audit_log_port = audit_log_port
    
    # ────────────────────── Use Cases ──────────────────────
    
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        currency: str = "EUR",
        method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        metadata: Optional[dict] = None,
    ) -> Payment:
        """
        Créer un paiement.
        
        Émet : PaymentCreatedEvent (Observer Pattern)
        """
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            currency=currency,
            method=method,
            metadata=metadata or {},
        )
        
        # Persister
        saved_payment = await self._repository.save(payment)
        
        # Émettre l'événement (notifie tous les subscribers)
        event = PaymentCreatedEvent(
            payment_id=saved_payment.id,
            booking_id=saved_payment.booking_id,
            amount=saved_payment.amount,
            currency=saved_payment.currency,
            method=saved_payment.method.value,
        )
        await self._event_publisher.publish(event)
        
        # Logs
        await self._system_log_port.log(
            level="INFO",
            message=f"Payment created: {saved_payment.id}",
            metadata={
                "payment_id": saved_payment.id,
                "booking_id": booking_id,
                "amount": amount,
            },
        )
        
        logger.info("Payment created", payment_id=saved_payment.id, booking_id=booking_id)
        return saved_payment
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Récupérer un paiement."""
        payment = await self._repository.find_by_id(payment_id)
        if not payment:
            logger.warning("Payment not found", payment_id=payment_id)
        return payment
    
    async def get_payments_by_booking(self, booking_id: str) -> list[Payment]:
        """Lister les paiements d'une réservation."""
        payments = await self._repository.find_by_booking(booking_id)
        logger.info("Fetched payments by booking", booking_id=booking_id, count=len(payments))
        return payments
    
    async def process_payment(self, payment_id: str) -> Payment:
        """
        Traiter un paiement auprès du provider.
        
        Transitions d'état : PENDING → PROCESSING → PAID ou FAILED
        Émet : PaymentProcessingStartedEvent, PaymentPaidEvent ou PaymentFailedEvent
        """
        payment = await self._repository.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if not payment.is_pending():
            raise ValueError(f"Cannot process payment in {payment.status.value} state")
        
        # Transition 1 : PENDING → PROCESSING
        payment.mark_processing()
        await self._repository.save(payment)
        
        event = PaymentProcessingStartedEvent(
            payment_id=payment.id,
            booking_id=payment.booking_id,
        )
        await self._event_publisher.publish(event)
        
        logger.info("Payment processing started", payment_id=payment_id)
        
        # Appel au provider externe (Stripe, PayPal, etc.)
        try:
            result = await self._payment_provider.process_payment(
                payment_id=payment_id,
                amount=payment.amount,
                currency=payment.currency,
                method=payment.method.value,
                metadata=payment.metadata,
            )
            
            if result.get("success"):
                # Transition 2 : PROCESSING → PAID
                payment.mark_paid()
                await self._repository.save(payment)
                
                # Émettre l'événement PaymentPaidEvent
                # Cet événement sera consommé par booking-service, notification, analytics, etc.
                event = PaymentPaidEvent(
                    payment_id=payment.id,
                    booking_id=payment.booking_id,
                    amount=payment.amount,
                    currency=payment.currency,
                )
                await self._event_publisher.publish(event)
                
                # Logs
                await self._system_log_port.log(
                    level="INFO",
                    message=f"Payment successful: {payment_id}",
                    metadata={"transaction_id": result.get("transaction_id")},
                )
                
                logger.info("Payment confirmed", payment_id=payment_id)
                return payment
            else:
                # Transition : PROCESSING → FAILED
                error_msg = result.get("error_message", "Unknown error")
                payment.mark_failed(error_msg)
                await self._repository.save(payment)
                
                event = PaymentFailedEvent(
                    payment_id=payment.id,
                    booking_id=payment.booking_id,
                    error_message=error_msg,
                    error_code=result.get("error_code", ""),
                )
                await self._event_publisher.publish(event)
                
                await self._system_log_port.log(
                    level="WARNING",
                    message=f"Payment failed: {payment_id}",
                    metadata={"error": error_msg},
                )
                
                logger.warning("Payment failed", payment_id=payment_id, error=error_msg)
                return payment
        
        except Exception as e:
            # Erreur lors du traitement (timeout, connexion, etc.)
            payment.mark_failed(str(e))
            await self._repository.save(payment)
            
            event = PaymentFailedEvent(
                payment_id=payment.id,
                booking_id=payment.booking_id,
                error_message=str(e),
                error_code="PROVIDER_ERROR",
            )
            await self._event_publisher.publish(event)
            
            logger.error("Payment provider error", payment_id=payment_id, error=str(e))
            raise
    
    async def confirm_payment(self, payment_id: str) -> Payment:
        """Confirmer manuellement qu'un paiement est validé."""
        payment = await self._repository.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if payment.status == PaymentStatus.PAID:
            logger.info("Payment already confirmed", payment_id=payment_id)
            return payment
        
        payment.mark_paid()
        await self._repository.save(payment)
        
        event = PaymentPaidEvent(
            payment_id=payment.id,
            booking_id=payment.booking_id,
            amount=payment.amount,
            currency=payment.currency,
        )
        await self._event_publisher.publish(event)
        
        logger.info("Payment manually confirmed", payment_id=payment_id)
        return payment
    
    async def cancel_payment(self, payment_id: str) -> Payment:
        """Annuler un paiement."""
        payment = await self._repository.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if payment.status in [PaymentStatus.PAID, PaymentStatus.REFUNDED]:
            raise ValueError(f"Cannot cancel payment in {payment.status.value} state")
        
        payment.mark_cancelled()
        await self._repository.save(payment)
        
        event = PaymentCancelledEvent(
            payment_id=payment.id,
            booking_id=payment.booking_id,
            reason="User cancelled",
        )
        await self._event_publisher.publish(event)
        
        await self._audit_log_port.log_action(
            user_id="system",
            action="CANCEL_PAYMENT",
            entity="Payment",
            entity_id=payment_id,
        )
        
        logger.info("Payment cancelled", payment_id=payment_id)
        return payment
    
    async def refund_payment(
        self,
        payment_id: str,
        refund_amount: Optional[float] = None,
    ) -> Payment:
        """
        Rembourser un paiement.
        
        Émet : PaymentRefundedEvent (Observer Pattern)
        """
        payment = await self._repository.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        if not payment.can_refund():
            raise ValueError(f"Cannot refund payment in {payment.status.value} state")
        
        # Montant par défaut : total du paiement
        actual_refund = refund_amount or payment.amount
        
        # Appel au provider pour effectuer le remboursement
        refund_result = await self._payment_provider.refund_payment(
            transaction_id=payment.metadata.get("transaction_id", ""),
            amount=actual_refund,
            currency=payment.currency,
        )
        
        if not refund_result.get("success"):
            raise ValueError(f"Refund failed: {refund_result.get('error_message')}")
        
        # Mettre à jour le paiement
        payment.mark_refunded(actual_refund)
        await self._repository.save(payment)
        
        # Émettre l'événement
        event = PaymentRefundedEvent(
            payment_id=payment.id,
            booking_id=payment.booking_id,
            refund_amount=actual_refund,
            refund_percentage=payment.refund_percentage(),
        )
        await self._event_publisher.publish(event)
        
        await self._audit_log_port.log_action(
            user_id="system",
            action="REFUND_PAYMENT",
            entity="Payment",
            entity_id=payment_id,
            details={"refund_amount": actual_refund},
        )
        
        logger.info("Payment refunded", payment_id=payment_id, refund_amount=actual_refund)
        return payment
    
    async def list_payments(
        self,
        status: Optional[PaymentStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """Lister les paiements avec filtres."""
        if status:
            payments = await self._repository.find_by_status(status, limit, offset)
        else:
            # TODO : implémenter find_all si nécessaire
            payments = []
        
        logger.info("Payments listed", status=status.value if status else None, count=len(payments))
        return payments
