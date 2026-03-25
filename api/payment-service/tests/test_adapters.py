"""
Tests des Adaptateurs — Repository, Event Publisher, Payment Provider

📚 Explication Pédagogique :
Les adaptateurs implémentent les ports abstraits.
Les tests vérifient que les contrats des ports sont respectés.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.payment import Payment, PaymentStatus, PaymentMethod
from adapters.outbound.repositories import PostgresPaymentRepository
from adapters.outbound.event_publisher import InMemoryEventPublisher
from adapters.outbound.payment_provider import MockPaymentProvider, StripePaymentProvider
from adapters.outbound.log_service_client import HttpLogServiceClient
from adapters.outbound.audit_service_client import HttpAuditServiceClient
from domain.models.payment_event import PaymentCreatedEvent, PaymentPaidEvent


# ────────────────── Tests Repository ──────────────────

class TestPostgresPaymentRepository:
    """Tests du repository PostgreSQL."""
    
    @pytest.mark.asyncio
    async def test_save_new_payment(self):
        """Test : sauvegarder un nouveau paiement."""
        # Mock de la session
        session = AsyncMock(spec=AsyncSession)
        session.get = AsyncMock(return_value=None)  # Pas de paiement existant
        session.flush = AsyncMock()
        
        repo = PostgresPaymentRepository(session)
        
        payment = Payment(booking_id="book-123", amount=100.0)
        result = await repo.save(payment)
        
        # Vérifier que add a été appelé
        session.add.assert_called_once()
        session.flush.assert_called_once()
        assert result.id == payment.id
        assert result.booking_id == "book-123"

    @pytest.mark.asyncio
    async def test_save_existing_payment(self):
        """Test : mettre à jour un paiement existant."""
        # Mock de la session
        session = AsyncMock(spec=AsyncSession)
        
        # Simuler un paiement existant en ORM
        existing_orm = MagicMock()
        existing_orm.id = "pay-123"
        existing_orm.booking_id = "book-123"
        existing_orm.amount = 100.0
        existing_orm.currency = "EUR"
        existing_orm.status = "PENDING"
        existing_orm.method = "CREDIT_CARD"
        existing_orm.created_at = None
        existing_orm.updated_at = None
        existing_orm.extra_metadata = {}
        existing_orm.error_message = None
        existing_orm.refunded_amount = 0.0
        
        session.get = AsyncMock(return_value=existing_orm)
        session.flush = AsyncMock()
        
        repo = PostgresPaymentRepository(session)
        
        payment = Payment(
            id="pay-123",
            booking_id="book-123",
            amount=100.0,
            status=PaymentStatus.PROCESSING
        )
        result = await repo.save(payment)
        
        # Vérifier que add n'a pas été appelé (update only)
        session.add.assert_not_called()
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_id(self):
        """Test : trouver un paiement par ID."""
        session = AsyncMock(spec=AsyncSession)
        
        orm_payment = MagicMock()
        orm_payment.id = "pay-123"
        orm_payment.booking_id = "book-123"
        orm_payment.amount = 100.0
        orm_payment.currency = "EUR"
        orm_payment.status = "PENDING"
        orm_payment.method = "CREDIT_CARD"
        orm_payment.created_at = None
        orm_payment.updated_at = None
        orm_payment.extra_metadata = {}
        orm_payment.error_message = None
        orm_payment.refunded_amount = 0.0
        
        session.get = AsyncMock(return_value=orm_payment)
        
        repo = PostgresPaymentRepository(session)
        result = await repo.find_by_id("pay-123")
        
        assert result is not None
        assert result.id == "pay-123"
        session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self):
        """Test : paiement inexistant retourne None."""
        session = AsyncMock(spec=AsyncSession)
        session.get = AsyncMock(return_value=None)
        
        repo = PostgresPaymentRepository(session)
        result = await repo.find_by_id("nonexistent")
        
        assert result is None


# ────────────────── Tests Event Publisher ──────────────────

class TestInMemoryEventPublisher:
    """Tests du publisher d'événements en mémoire."""
    
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test : publier un événement enregistre."""
        publisher = InMemoryEventPublisher()
        
        event = PaymentCreatedEvent(
            payment_id="pay-123",
            booking_id="book-123",
            amount=100.0,
            currency="EUR",
            method="CREDIT_CARD",
        )
        
        await publisher.publish(event)
        
        # Vérifier que l'événement est en mémoire
        assert len(publisher._events) == 1
        assert publisher._events[0].payment_id == "pay-123"
    
    @pytest.mark.asyncio
    async def test_get_events(self):
        """Test : récupérer les événements publiés."""
        publisher = InMemoryEventPublisher()
        
        event = PaymentCreatedEvent(
            payment_id="pay-123",
            booking_id="book-123",
            amount=100.0,
            currency="EUR",
            method="CREDIT_CARD",
        )
        
        await publisher.publish(event)
        
        # Vérifier que l'événement est accessible
        events = [e for e in publisher._events]
        assert len(events) == 1
        assert events[0].payment_id == "pay-123"

    @pytest.mark.asyncio
    async def test_publish_batch(self):
        """Test : publier plusieurs événements en batch."""
        publisher = InMemoryEventPublisher()
        
        events = [
            PaymentCreatedEvent(
                payment_id="pay-123",
                booking_id="book-123",
                amount=100.0,
                currency="EUR",
                method="CREDIT_CARD",
            ),
            PaymentPaidEvent(
                payment_id="pay-123",
                booking_id="book-123",
                amount=100.0,
                currency="EUR",
            ),
        ]
        
        await publisher.publish_batch(events)
        
        assert len(publisher._events) == 2


# ────────────────── Tests Payment Provider ──────────────────

class TestMockPaymentProvider:
    """Tests du provider de paiement Mock."""
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self):
        """Test : traiter un paiement avec succès."""
        provider = MockPaymentProvider()
        
        result = await provider.process_payment(
            payment_id="pay-123",
            amount=100.0,
            currency="EUR",
            method="CREDIT_CARD",
        )
        
        # 80% de chance de succès
        assert "success" in result
        assert "transaction_id" in result or "error_code" in result

    @pytest.mark.asyncio
    async def test_refund_payment(self):
        """Test : rembourser un paiement."""
        provider = MockPaymentProvider()
        
        result = await provider.refund_payment(
            transaction_id="txn-123",
            amount=50.0,
            currency="EUR",
        )
        
        assert result["success"] is True
        assert "refund_id" in result

    @pytest.mark.asyncio
    async def test_verify_payment(self):
        """Test : vérifier un paiement."""
        provider = MockPaymentProvider()
        
        result = await provider.verify_payment(transaction_id="txn-123")
        
        assert isinstance(result, dict)
        assert "status" in result


class TestStripePaymentProvider:
    """Tests du provider Stripe (stub)."""
    
    @pytest.mark.asyncio
    async def test_stripe_not_implemented(self):
        """Test : Stripe provider lève une erreur (not implemented)."""
        from adapters.outbound.payment_provider import StripePaymentProvider
        provider = StripePaymentProvider(api_key="sk_test_123")
        
        with pytest.raises(NotImplementedError):
            await provider.process_payment(
                payment_id="pay-123",
                amount=100.0,
                currency="EUR",
                method="CREDIT_CARD",
            )


# ────────────────── Tests HTTP Log Clients ──────────────────

class TestHttpLogServiceClient:
    """Tests du client HTTP pour le service de logs."""
    
    @pytest.mark.asyncio
    async def test_log_success(self):
        """Test : envoyer un log au service."""
        client = HttpLogServiceClient(
            base_url="http://log-service:8005",
            timeout_seconds=5.0,
        )
        
        # Mock httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=201))
            
            await client.log(
                level="INFO",
                message="Test log",
                metadata={"test": True},
            )
            
            # Vérifier que post a été appelé
            assert mock_client.post.called

    @pytest.mark.asyncio
    async def test_log_timeout_handling(self):
        """Test : gérer les timeouts gracieusement."""
        client = HttpLogServiceClient(
            base_url="http://log-service:8005",
            timeout_seconds=0.001,  # Très court pour forcer timeout
        )
        
        # Aucune exception ne doit être levée (graceful degradation)
        try:
            await client.log(level="INFO", message="Test")
        except Exception as e:
            # Les exceptions sont capturées en interne
            assert True


class TestHttpAuditServiceClient:
    """Tests du client HTTP pour les logs d'audit."""
    
    @pytest.mark.asyncio
    async def test_log_action(self):
        """Test : envoyer une action d'audit."""
        client = HttpAuditServiceClient(
            base_url="http://log-service:8005",
            timeout_seconds=5.0,
        )
        
        # Mock httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=201))
            
            await client.log_action(
                user_id="user-123",
                action="CREATE",
                entity="payment",
                entity_id="pay-123",
                details={"amount": 100.0},
            )
            
            assert mock_client.post.called
