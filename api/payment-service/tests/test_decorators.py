"""
Tests des Décorateurs — DECORATOR PATTERN

📚 Explication Pédagogique :
Les décorateurs permettent d'enrichir le service métier.
On teste que :
1. Logging fonctionne
2. Validations supplémentaires fonctionnent
3. Métriques sont collectées
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from domain.models.payment import PaymentStatus, PaymentMethod
from domain.services.payment_service import PaymentService
from domain.services.payment_decorators import (
    PaymentLoggingDecorator, PaymentValidationDecorator, PaymentMetricsDecorator,
)


# Mock repositories & ports
class MockRepository:
    async def save(self, payment):
        return payment
    async def find_by_id(self, payment_id):
        return None
    async def find_by_booking(self, booking_id):
        return []
    async def find_by_status(self, status, limit, offset):
        return []


class MockEventPublisher:
    async def publish(self, event):
        pass
    async def publish_batch(self, events):
        pass


class MockPaymentProvider:
    async def process_payment(self, **kwargs):
        return {"success": True, "transaction_id": "txn-123"}
    async def refund_payment(self, **kwargs):
        return {"success": True}
    async def verify_payment(self, **kwargs):
        return {"success": True}


class MockLogPort:
    async def log(self, **kwargs):
        pass


class MockAuditPort:
    async def log_action(self, **kwargs):
        pass


def create_service():
    """Créer un service avec des mocks."""
    return PaymentService(
        repository=MockRepository(),
        event_publisher=MockEventPublisher(),
        payment_provider=MockPaymentProvider(),
        system_log_port=MockLogPort(),
        audit_log_port=MockAuditPort(),
    )


# ────────────────── Tests Decorators ──────────────────

class TestLoggingDecorator:
    """Tests pour le PaymentLoggingDecorator."""
    
    @pytest.mark.asyncio
    async def test_logging_on_success(self):
        """Test : logging lors du succès."""
        service = create_service()
        service = PaymentLoggingDecorator(service)
        
        payment = await service.create_payment(
            booking_id="book-123",
            amount=100.0,
        )
        
        assert payment.id is not None
        assert payment.booking_id == "book-123"
    
    @pytest.mark.asyncio
    async def test_logging_on_error(self):
        """Test : logging lors d'une erreur."""
        service = create_service()
        service = PaymentLoggingDecorator(service)
        
        # Créer avec montant invalide
        with pytest.raises(ValueError):
            await service.create_payment(
                booking_id="book-123",
                amount=-50.0,
            )


class TestValidationDecorator:
    """Tests pour le PaymentValidationDecorator."""
    
    @pytest.mark.asyncio
    async def test_validation_amount(self):
        """Test : validation du montant."""
        service = create_service()
        service = PaymentValidationDecorator(service)
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            await service.create_payment(
                booking_id="book-123",
                amount=-10.0,
            )
    
    @pytest.mark.asyncio
    async def test_validation_booking_id(self):
        """Test : validation du booking_id."""
        service = create_service()
        service = PaymentValidationDecorator(service)
        
        with pytest.raises(ValueError, match="booking_id required"):
            await service.create_payment(
                booking_id="",
                amount=100.0,
            )
    
    @pytest.mark.asyncio
    async def test_validation_refund_amount(self):
        """Test : validation du montant de remboursement."""
        service = create_service()
        service = PaymentValidationDecorator(service)
        
        with pytest.raises(ValueError):
            await service.refund_payment(
                payment_id="pay-123",
                refund_amount=-10.0,
            )


class TestMetricsDecorator:
    """Tests pour le PaymentMetricsDecorator."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test : collecte des métriques."""
        service = create_service()
        metrics_decorator = PaymentMetricsDecorator(service)
        
        # Créer un paiement
        await metrics_decorator.create_payment(
            booking_id="book-123",
            amount=100.0,
        )
        
        # Vérifier les métriques
        metrics = metrics_decorator.get_metrics()
        assert metrics["created_count"] == 1
        assert metrics["errors_count"] == 0
    
    @pytest.mark.asyncio
    async def test_metrics_error_count(self):
        """Test : comptage des erreurs."""
        service = create_service()
        metrics_decorator = PaymentMetricsDecorator(service)
        
        # Essayer de créer avec montant invalide
        try:
            await metrics_decorator.create_payment(
                booking_id="book-123",
                amount=-50.0,
            )
        except ValueError:
            pass
        
        metrics = metrics_decorator.get_metrics()
        assert metrics["errors_count"] == 1


# ────────────────── Tests Chaining Decorators ──────────────────

class TestDecoratorChaining:
    """Tests pour le chaînage des décorateurs."""
    
    @pytest.mark.asyncio
    async def test_multiple_decorators(self):
        """Test : application de multiples décorateurs."""
        service = create_service()
        service = PaymentLoggingDecorator(service)
        service = PaymentValidationDecorator(service)
        service = PaymentMetricsDecorator(service)
        
        # Doit fonctionner avec tous les décorateurs
        payment = await service.create_payment(
            booking_id="book-123",
            amount=100.0,
        )
        
        assert payment.booking_id == "book-123"
