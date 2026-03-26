"""
Tests des Routes API — Adaptateur Inbound

📚 Explication Pédagogique :
Les tests des routes vérifient que :
1. Les endpoints répondent avec le bon status code
2. Les données de réponse sont valides
3. Les erreurs sont gérées correctement
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adapters.inbound import routes as routes_module
from adapters.inbound.routes import router
from domain.models.payment import Payment, PaymentStatus
from infrastructure.database import get_db_session


class DummyPaymentService:
    """Service factice pour les tests des routes."""
    
    def __init__(self):
        self.payments = {}
    
    async def create_payment(self, booking_id, amount, currency="EUR", method=None, metadata=None):
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            currency=currency,
        )
        self.payments[payment.id] = payment
        return payment
    
    async def get_payment(self, payment_id):
        return self.payments.get(payment_id)
    
    async def get_payments_by_booking(self, booking_id):
        return [p for p in self.payments.values() if p.booking_id == booking_id]
    
    async def process_payment(self, payment_id):
        payment = self.payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        payment.mark_paid()
        self.payments[payment.id] = payment
        return payment
    
    async def confirm_payment(self, payment_id):
        payment = self.payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        payment.mark_paid()
        return payment
    
    async def cancel_payment(self, payment_id):
        payment = self.payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        payment.mark_cancelled()
        return payment
    
    async def refund_payment(self, payment_id, refund_amount=None):
        payment = self.payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        payment.mark_refunded(refund_amount or payment.amount)
        return payment
    
    async def list_payments(self, status=None, limit=100, offset=0):
        return list(self.payments.values())[:limit]


@pytest.fixture
def test_app(monkeypatch):
    """Créer une app FastAPI avec dépendances mockées."""
    app = FastAPI()
    app.include_router(router)
    
    async def fake_db_session():
        yield None
    
    app.dependency_overrides[get_db_session] = fake_db_session
    
    service = DummyPaymentService()
    monkeypatch.setattr(routes_module, "get_payment_service", lambda db: service)
    
    return app, service


def test_create_payment_success(test_app):
    """Test : créer un paiement avec succès."""
    app, _ = test_app
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/payments/",
        json={
            "booking_id": "book-123",
            "amount": 100.0,
            "currency": "EUR",
            "method": "CREDIT_CARD",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == "book-123"
    assert data["amount"] == 100.0
    assert data["status"] == "PENDING"


def test_create_payment_invalid_amount(test_app):
    """Test : montant invalide → 422 (Pydantic validation)."""
    app, _ = test_app
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/payments/",
        json={
            "booking_id": "book-123",
            "amount": -50.0,  # Invalide
            "currency": "EUR",
        },
    )
    
    assert response.status_code == 422


def test_get_payment_success(test_app):
    """Test : récupérer un paiement."""
    app, service = test_app
    client = TestClient(app)
    
    # Créer d'abord un paiement
    payment = __create_payment(client)
    payment_id = payment["id"]
    
    # Récupérer
    response = client.get(f"/api/v1/payments/{payment_id}")
    assert response.status_code == 200
    assert response.json()["id"] == payment_id


def test_get_payment_not_found(test_app):
    """Test : paiement inexistant → 404."""
    app, _ = test_app
    client = TestClient(app)
    
    response = client.get("/api/v1/payments/nonexistent")
    assert response.status_code == 404


def test_list_payments_by_booking(test_app):
    """Test : lister les paiements d'une réservation."""
    app, _ = test_app
    client = TestClient(app)
    
    # Créer 2 paiements pour la même réservation
    __create_payment(client, booking_id="book-123")
    __create_payment(client, booking_id="book-123")
    __create_payment(client, booking_id="book-456")
    
    # Lister
    response = client.get("/api/v1/payments/booking/book-123")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_process_payment_success(test_app):
    """Test : traiter un paiement."""
    app, _ = test_app
    client = TestClient(app)
    
    payment = __create_payment(client)
    payment_id = payment["id"]
    
    # Traiter
    response = client.post(f"/api/v1/payments/{payment_id}/process")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PAID"


def test_process_payment_not_found(test_app):
    """Test : traiter un paiement inexistant."""
    app, _ = test_app
    client = TestClient(app)
    
    response = client.post("/api/v1/payments/nonexistent/process")
    assert response.status_code == 400


def test_cancel_payment(test_app):
    """Test : annuler un paiement."""
    app, _ = test_app
    client = TestClient(app)
    
    payment = __create_payment(client)
    payment_id = payment["id"]
    
    response = client.post(f"/api/v1/payments/{payment_id}/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CANCELLED"


def test_refund_payment(test_app):
    """Test : rembourser un paiement."""
    app, _ = test_app
    client = TestClient(app)
    
    payment = __create_payment(client)
    payment_id = payment["id"]
    
    # Traiter d'abord
    client.post(f"/api/v1/payments/{payment_id}/process")
    
    # Rembourser
    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        json={"refund_amount": 50.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REFUNDED" or data["status"] == "PAID"
    assert data["refunded_amount"] == 50.0


def test_health_check(test_app):
    """Test : vérifier la santé du service."""
    app, _ = test_app
    client = TestClient(app)
    
    response = client.get("/api/v1/payments/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]


# ────────────────── Helpers ──────────────────

def __create_payment(client, booking_id="book-123", amount=100.0):
    """Helper pour créer un paiement de test."""
    response = client.post(
        "/api/v1/payments/",
        json={
            "booking_id": booking_id,
            "amount": amount,
            "currency": "EUR",
            "method": "CREDIT_CARD",
        },
    )
    assert response.status_code == 201
    return response.json()
