"""
Tests Unitaires — Domain Layer

📚 Explication Pédagogique :
Les tests du domaine sont LES PLUS IMPORTANTS.
Ils testent la logique métier SANS DB, SANS API.

C'est le grand avantage de l'architecture hexagonale :
→ Le domaine est testable en isolation
→ Pas besoin de Docker, pas besoin de PostgreSQL
→ Les tests sont rapides (millisecondes)
"""
import pytest
from datetime import datetime

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from domain.models.payment_event import (
    PaymentCreatedEvent, PaymentPaidEvent, PaymentFailedEvent, PaymentRefundedEvent,
)


# ────────────────── Tests Payment Entity ──────────────────

class TestPaymentEntity:
    """Tests unitaires pour l'entité Payment."""
    
    def test_create_payment_valid(self):
        """Test : créer un paiement valide."""
        payment = Payment(
            booking_id="book-123",
            amount=100.0,
            currency="EUR",
            method=PaymentMethod.CREDIT_CARD,
        )
        
        assert payment.booking_id == "book-123"
        assert payment.amount == 100.0
        assert payment.status == PaymentStatus.PENDING
        assert payment.id is not None
    
    def test_create_payment_invalid_amount(self):
        """Test : montant invalide."""
        with pytest.raises(ValueError, match="amount doit être > 0"):
            Payment(booking_id="book-123", amount=-50.0)
    
    def test_create_payment_missing_booking_id(self):
        """Test : booking_id vide."""
        with pytest.raises(ValueError, match="booking_id est obligatoire"):
            Payment(booking_id="", amount=100.0)
    
    def test_mark_processing(self):
        """Test : transition PENDING → PROCESSING."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_processing()
        
        assert payment.status == PaymentStatus.PROCESSING
    
    def test_mark_processing_invalid_state(self):
        """Test : impossible de marquer PROCESSING depuis PAID."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        
        with pytest.raises(ValueError, match="Impossible de passer à PROCESSING"):
            payment.mark_processing()
    
    def test_mark_paid(self):
        """Test : transition PENDING → PAID."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        
        assert payment.status == PaymentStatus.PAID
        assert payment.is_paid() is True
    
    def test_mark_failed(self):
        """Test : marquer comme échoué."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_failed("Card declined")
        
        assert payment.status == PaymentStatus.FAILED
        assert payment.error_message == "Card declined"
    
    def test_mark_cancelled(self):
        """Test : annuler un paiement."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_cancelled()
        
        assert payment.status == PaymentStatus.CANCELLED
    
    def test_mark_refunded_full(self):
        """Test : remboursement total."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        payment.mark_refunded(100.0)
        
        assert payment.status == PaymentStatus.REFUNDED
        assert payment.refunded_amount == 100.0
        assert payment.refund_percentage() == 100.0
    
    def test_mark_refunded_partial(self):
        """Test : remboursement partiel."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        payment.mark_refunded(30.0)
        
        assert payment.refunded_amount == 30.0
        assert payment.refund_percentage() == 30.0
    
    def test_mark_refunded_invalid_state(self):
        """Test : impossible de rembourser depuis PENDING."""
        payment = Payment(booking_id="book-123", amount=100.0)
        
        with pytest.raises(ValueError, match="Impossible de rembourser"):
            payment.mark_refunded(50.0)
    
    def test_can_refund(self):
        """Test : vérifier si remboursable."""
        payment = Payment(booking_id="book-123", amount=100.0)
        
        assert payment.can_refund() is False  # PENDING
        
        payment.mark_paid()
        assert payment.can_refund() is True  # PAID
        
        payment.mark_refunded(100.0)
        assert payment.can_refund() is False  # REFUNDED
    
    def test_is_terminal_state(self):
        """Test : vérifier les états terminaux."""
        payment = Payment(booking_id="book-123", amount=100.0)
        
        assert payment.is_terminal_state() is False  # PENDING
        
        payment.mark_paid()
        assert payment.is_terminal_state() is True  # PAID
    
    def test_to_dict(self):
        """Test : sérialisation en dict."""
        payment = Payment(
            booking_id="book-123",
            amount=100.0,
            metadata={"user_id": "user-1"},
        )
        
        d = payment.to_dict()
        
        assert d["booking_id"] == "book-123"
        assert d["amount"] == 100.0
        assert d["status"] == "PENDING"
        assert d["metadata"]["user_id"] == "user-1"


# ────────────────── Tests Payment Events ──────────────────

class TestPaymentEvents:
    """Tests unitaires pour les événements de paiement."""
    
    def test_payment_created_event(self):
        """Test : créer un PaymentCreatedEvent."""
        event = PaymentCreatedEvent(
            payment_id="pay-123",
            booking_id="book-456",
            amount=100.0,
            currency="EUR",
            method="CREDIT_CARD",
        )
        
        assert event.payment_id == "pay-123"
        assert event.booking_id == "book-456"
        assert event.amount == 100.0
    
    def test_payment_paid_event(self):
        """Test : créer un PaymentPaidEvent."""
        event = PaymentPaidEvent(
            payment_id="pay-123",
            booking_id="book-456",
            amount=100.0,
        )
        
        d = event.to_dict()
        assert d["event_type"] == "PaymentPaidEvent"
        assert d["payment_id"] == "pay-123"
    
    def test_payment_failed_event(self):
        """Test : créer un PaymentFailedEvent."""
        event = PaymentFailedEvent(
            payment_id="pay-123",
            booking_id="book-456",
            error_message="Card declined",
            error_code="CARD_DECLINED",
        )
        
        assert event.error_message == "Card declined"
        assert event.error_code == "CARD_DECLINED"
    
    def test_payment_refunded_event(self):
        """Test : créer un PaymentRefundedEvent."""
        event = PaymentRefundedEvent(
            payment_id="pay-123",
            booking_id="book-456",
            refund_amount=50.0,
            refund_percentage=50.0,
        )
        
        assert event.refund_amount == 50.0
        assert event.refund_percentage == 50.0


# ────────────────── Tests State Transitions ──────────────────

class TestPaymentStateTransitions:
    """Tests des transitions d'état."""
    
    def test_valid_transitions(self):
        """Test : transitions valides."""
        payment = Payment(booking_id="book-123", amount=100.0)
        
        # PENDING → PROCESSING
        payment.mark_processing()
        assert payment.status == PaymentStatus.PROCESSING
        
        # PROCESSING → PAID
        payment.mark_paid()
        assert payment.status == PaymentStatus.PAID
        
        # PAID → REFUNDED
        payment.mark_refunded(100.0)
        assert payment.status == PaymentStatus.REFUNDED
    
    def test_invalid_transition_timing(self):
        """Test : transition impossible (déjà terminal)."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_paid()
        
        # Ne doit pas pouvoir passer à PROCESSING après PAID
        with pytest.raises(ValueError):
            payment.mark_processing()
    
    def test_alternative_path_cancel(self):
        """Test : chemin alternatif - annulation."""
        payment = Payment(booking_id="book-123", amount=100.0)
        payment.mark_cancelled()
        
        assert payment.status == PaymentStatus.CANCELLED
        assert payment.is_terminal_state() is True
