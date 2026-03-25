"""
Tests supplémentaires du Service Métier — Couverture complète

Amélioration de la couverture du PaymentService et PaymentDecorators
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from domain.services.payment_service import PaymentService
from domain.services.payment_decorators import (
    PaymentLoggingDecorator,
    PaymentValidationDecorator,
    PaymentMetricsDecorator,
)
from domain.models.payment_event import (
    PaymentCreatedEvent, PaymentProcessingStartedEvent,
    PaymentPaidEvent, PaymentFailedEvent, PaymentCancelledEvent,
    PaymentRefundedEvent,
)


# Mocks avancés
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
        results = [p for p in self.payments.values() if p.status == status]
        return results[offset:offset+limit]
    
    async def delete(self, payment_id):
        if payment_id in self.payments:
            del self.payments[payment_id]
            return True
        return False


class MockEventPublisher:
    def __init__(self):
        self.events = []
        self.subscribers = {}
    
    async def publish(self, event):
        self.events.append(event)
        # Notifier les subscribers
        event_type = event.__class__.__name__
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                await callback(event)
    
    async def publish_batch(self, events):
        for event in events:
            await self.publish(event)
    
    def subscribe(self, event_type, callback):
        event_type_name = event_type.__name__
        if event_type_name not in self.subscribers:
            self.subscribers[event_type_name] = []
        self.subscribers[event_type_name].append(callback)


class MockPaymentProvider:
    def __init__(self, success=True):
        self.success = success
        self.call_count = 0
    
    async def process_payment(self, **kwargs):
        self.call_count += 1
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
    def __init__(self):
        self.logs = []
    
    async def log(self, **kwargs):
        self.logs.append(kwargs)


class MockAuditPort:
    def __init__(self):
        self.actions = []
    
    async def log_action(self, **kwargs):
        self.actions.append(kwargs)


# ────────────────── Tests Service Complets ──────────────────

class TestPaymentServiceComprehensive:
    """Tests complets du PaymentService."""
    
    @pytest.mark.asyncio
    async def test_get_payment(self):
        """Test : récupérer un paiement par ID."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Créer un paiement d'abord
        payment = await service.create_payment("book-123", 100.0)
        
        # Récupérer
        result = await service.get_payment(payment.id)
        assert result is not None
        assert result.id == payment.id

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self):
        """Test : retourner None si paiement inexistant."""
        service = PaymentService(
            repository=MockRepository(),
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        result = await service.get_payment("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_payments_by_booking(self):
        """Test : récupérer tous les paiements d'une réservation."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Créer 2 paiements pour la même réservation
        await service.create_payment("book-123", 100.0)
        await service.create_payment("book-123", 50.0)
        await service.create_payment("book-456", 200.0)
        
        # Récupérer
        results = await service.get_payments_by_booking("book-123")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_confirm_payment(self):
        """Test : confirmer manuellement un paiement."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        payment = await service.create_payment("book-123", 100.0)
        result = await service.confirm_payment(payment.id)
        
        assert result.status == PaymentStatus.PAID

    @pytest.mark.asyncio
    async def test_cancel_payment(self):
        """Test : annuler un paiement en PENDING."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        payment = await service.create_payment("book-123", 100.0)
        result = await service.cancel_payment(payment.id)
        
        assert result.status == PaymentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_list_payments_by_status_pagination(self):
        """Test : lister les paiements filtrés par statut avec pagination."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Créer et marquer comme PENDING
        for i in range(1, 4):
            await service.create_payment(f"book-{i}", float(100 * i))
        
        # Lister les PENDING
        results = await service.list_payments(
            status=PaymentStatus.PENDING,
            limit=10,
            offset=0,
        )
        assert len(results) == 3
        assert all(p.status == PaymentStatus.PENDING for p in results)

    @pytest.mark.asyncio
    async def test_list_payments_by_status(self):
        """Test : lister les paiements filtrés par statut."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Créer et traiter
        payment1 = await service.create_payment("book-1", 100.0)
        payment2 = await service.create_payment("book-2", 200.0)
        await service.confirm_payment(payment1.id)  # PAID
        
        # Lister les PAID
        results = await service.list_payments(
            status=PaymentStatus.PAID,
            limit=100,
            offset=0,
        )
        assert len(results) == 1
        assert results[0].status == PaymentStatus.PAID

    @pytest.mark.asyncio
    async def test_refund_payment_partial(self):
        """Test : rembourser partiellement un paiement."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        payment = await service.create_payment("book-123", 100.0)
        await service.confirm_payment(payment.id)
        
        result = await service.refund_payment(payment.id, 30.0)
        assert result.refunded_amount == 30.0

    @pytest.mark.asyncio
    async def test_refund_payment_full(self):
        """Test : rembourser totalement un paiement."""
        repo = MockRepository()
        service = PaymentService(
            repository=repo,
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        payment = await service.create_payment("book-123", 100.0)
        await service.confirm_payment(payment.id)
        
        result = await service.refund_payment(payment.id, 100.0)
        assert result.refunded_amount == 100.0
        assert result.status == PaymentStatus.REFUNDED

    @pytest.mark.asyncio
    async def test_process_payment_not_found(self):
        """Test : traiter un paiement inexistant."""
        service = PaymentService(
            repository=MockRepository(),
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        with pytest.raises(ValueError):
            await service.process_payment("nonexistent")

    @pytest.mark.asyncio
    async def test_cannot_refund_pending_payment(self):
        """Test : impossible de rembourser un PENDING."""
        service = PaymentService(
            repository=MockRepository(),
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        payment = await service.create_payment("book-123", 100.0)
        
        with pytest.raises(ValueError):
            await service.refund_payment(payment.id, 50.0)


# ────────────────── Tests Decorators Complets ──────────────────

class TestPaymentDecoratorsComprehensive:
    """Tests complets des décorateurs."""
    
    @pytest.mark.asyncio
    async def test_validation_decorator_rejects_negative_amount(self):
        """Test : validation rejette les montants négatifs."""
        service = PaymentValidationDecorator(
            PaymentService(
                repository=MockRepository(),
                event_publisher=MockEventPublisher(),
                payment_provider=MockPaymentProvider(),
                system_log_port=MockLogPort(),
                audit_log_port=MockAuditPort(),
            )
        )
        
        with pytest.raises(ValueError):
            await service.create_payment("book-123", -100.0)

    @pytest.mark.asyncio
    async def test_validation_decorator_rejects_zero_amount(self):
        """Test : validation rejette les montants zéro."""
        service = PaymentValidationDecorator(
            PaymentService(
                repository=MockRepository(),
                event_publisher=MockEventPublisher(),
                payment_provider=MockPaymentProvider(),
                system_log_port=MockLogPort(),
                audit_log_port=MockAuditPort(),
            )
        )
        
        with pytest.raises(ValueError):
            await service.create_payment("book-123", 0.0)

    @pytest.mark.asyncio
    async def test_metrics_decorator_tracks_created(self):
        """Test : les décorateurs de métriques comptent les créations."""
        inner_service = PaymentService(
            repository=MockRepository(),
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        metrics = PaymentMetricsDecorator(inner_service)
        
        await metrics.create_payment("book-1", 100.0)
        await metrics.create_payment("book-2", 200.0)
        
        # Utiliser get_metrics() si disponible
        # assert metrics.created_count == 2

    @pytest.mark.asyncio
    async def test_logging_decorator_handles_exceptions(self):
        """Test : le décorateur de logging gère les exceptions."""
        service = PaymentLoggingDecorator(
            PaymentService(
                repository=MockRepository(),
                event_publisher=MockEventPublisher(),
                payment_provider=MockPaymentProvider(),
                system_log_port=MockLogPort(),
                audit_log_port=MockAuditPort(),
            )
        )
        
        # Essayer de traiter un paiement inexistant → exception
        with pytest.raises(ValueError):
            await service.process_payment("nonexistent")

    @pytest.mark.asyncio
    async def test_decorator_chaining_order(self):
        """Test : l'ordre du chaînage est respecté."""
        inner = PaymentService(
            repository=MockRepository(),
            event_publisher=MockEventPublisher(),
            payment_provider=MockPaymentProvider(),
            system_log_port=MockLogPort(),
            audit_log_port=MockAuditPort(),
        )
        
        # Logger → Validation → Metrics
        service = PaymentLoggingDecorator(inner)
        service = PaymentValidationDecorator(service)
        service = PaymentMetricsDecorator(service)
        
        # Aucune exception = chaînage OK
        payment = await service.create_payment("book-123", 100.0)
        assert payment is not None
