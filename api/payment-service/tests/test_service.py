"""
Tests du Service Métier — PaymentService avec Observer Pattern

📚 Explication Pédagogique :
Les tests du service testent la logique métier orchestrée.
On utilise des mocks pour les ports (repository, event publisher, payment provider).
On teste que les événements sont publiés correctement (Observer Pattern).
"""
import pytest
from datetime import datetime

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from domain.services.payment_service import PaymentService
from domain.models.payment_event import (
    PaymentCreatedEvent, PaymentProcessingStartedEvent,
    PaymentPaidEvent, PaymentFailedEvent,
)


# Mocks pour les ports
class MockRepository:
    def __init__(self):
        self.payments = {}
    
    async def save(self, payment):
        self.payments[payment.id] = payment
        return payment
    
    async def find_by_id(self, payment_id):
        return self.payments.get(payment_id)
    
    async def find_by_booking(self, booking_id):
        return [p for p in self.payments.values() if p.booking_id == booking_id]
    
    async def find_by_status(self, status, limit, offset):
        return [p for p in self.payments.values() if p.status == status][:limit]
    
    async def delete(self, payment_id):
        if payment_id in self.payments:
            del self.payments[payment_id]
            return True
        return False


class MockEventPublisher:
    def __init__(self):
        self.events = []
    
    async def publish(self, event):
        self.events.append(event)
    
    async def publish_batch(self, events):
        self.events.extend(events)
    
    def get_events(self):
        return self.events.copy()


class MockPaymentProvider:
    def __init__(self, success=True):
        self.success = success
    
    async def process_payment(self, **kwargs):
        if self.success:
            return {
                "success": True,
                "transaction_id": f"txn_{kwargs['payment_id']}",
            }
        else:
            return {
                "success": False,
                "error_code": "CARD_DECLINED",
                "error_message": "Card declined",
            }
    
    async def refund_payment(self, **kwargs):
        return {"success": True, "refund_id": "refund-123"}
    
    async def verify_payment(self, **kwargs):
        return {"success": True}


class MockLogPort:
    async def log(self, **kwargs):
        pass


class MockAuditPort:
    async def log_action(self, **kwargs):
        pass


# ────────────────── Tests Service ──────────────────

class TestPaymentServiceObserver:
    """Tests du service avec Observer Pattern."""
    
    @pytest.mark.asyncio
    async def test_create_payment_publishes_event(self):
        """Test : créer un paiement publie PaymentCreatedEvent."""
        repository = MockRepository()
        event_publisher = MockEventPublisher()
        
        service = PaymentService(
            repository=repository,
            event_publisher=event_publisher,
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Créer un paiement
        payment = await service.create_payment(
            booking_id="book-123",
            amount=100.0,
        )
        
        # Vérifier que l'événement a été publié
        events = event_publisher.get_events()
        assert len(events) == 1
        assert isinstance(events[0], PaymentCreatedEvent)
        assert events[0].amount == 100.0
    
    @pytest.mark.asyncio
    async def test_process_payment_publishes_success_event(self):
        """Test : traiter un paiement réussi publie PaymentPaidEvent."""
        repository = MockRepository()
        event_publisher = MockEventPublisher()
        
        # Créer et sauvegarder un paiement
        payment = Payment(booking_id="book-123", amount=100.0)
        await repository.save(payment)
        
        service = PaymentService(
            repository=repository,
            event_publisher=event_publisher,
            payment_provider=MockPaymentProvider(success=True),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Traiter le paiement
        result = await service.process_payment(payment.id)
        
        # Vérifier les événements
        events = event_publisher.get_events()
        
        # Doit avoir : PaymentProcessingStartedEvent + PaymentPaidEvent
        assert len(events) == 2
        assert isinstance(events[0], PaymentProcessingStartedEvent)
        assert isinstance(events[1], PaymentPaidEvent)
        assert result.status == PaymentStatus.PAID
    
    @pytest.mark.asyncio
    async def test_process_payment_publishes_failure_event(self):
        """Test : traiter un paiement échoué publie PaymentFailedEvent."""
        repository = MockRepository()
        event_publisher = MockEventPublisher()
        
        payment = Payment(booking_id="book-123", amount=100.0)
        await repository.save(payment)
        
        service = PaymentService(
            repository=repository,
            event_publisher=event_publisher,
            payment_provider=MockPaymentProvider(success=False),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Traiter le paiement (échouera)
        result = await service.process_payment(payment.id)
        
        # Vérifier les événements
        events = event_publisher.get_events()
        assert len(events) == 2
        assert isinstance(events[1], PaymentFailedEvent)
        assert result.status == PaymentStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_refund_publishes_event(self):
        """Test : rembourser un paiement publie RefundedEvent."""
        repository = MockRepository()
        event_publisher = MockEventPublisher()
        
        # Créer un paiement validé
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        payment.metadata["transaction_id"] = "txn-123"
        await repository.save(payment)
        
        service = PaymentService(
            repository=repository,
            event_publisher=event_publisher,
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Rembourser
        result = await service.refund_payment(payment.id, 100.0)
        
        # Vérifier l'événement
        events = event_publisher.get_events()
        assert len(events) == 1
        assert result.status == PaymentStatus.REFUNDED


class TestPaymentServiceValidation:
    """Tests de validation du service."""
    
    @pytest.mark.asyncio
    async def test_process_nonexistent_payment(self):
        """Test : traiter un paiement inexistant."""
        repository = MockRepository()
        
        service = PaymentService(
            repository=repository,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        with pytest.raises(ValueError, match="not found"):
            await service.process_payment("nonexistent")
    
    @pytest.mark.asyncio
    async def test_cannot_process_paid_payment(self):
        """Test : impossible de traiter deux fois."""
        repository = MockRepository()
        
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        await repository.save(payment)
        
        service = PaymentService(
            repository=repository,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        with pytest.raises(ValueError):
            await service.process_payment(payment.id)
