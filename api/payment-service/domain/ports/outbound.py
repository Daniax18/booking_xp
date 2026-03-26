"""
Ports Outbound — Abstractions des dépendances externes

📚 Explication Pédagogique :
Les ports outbound définissent les dépendances du domaine :
- Où stocker les données (repository pattern)
- Comment communiquer avec les systèmes de paiement
- Comment notifier les autres services (event publisher)

Le domaine ne connaît pas les implémentations concrètes.
Les adaptateurs fourniront PostgreSQL, Stripe, HTTP, etc.
"""
from abc import ABC, abstractmethod
from typing import Optional

from domain.models.payment import Payment, PaymentStatus
from domain.models.payment_event import PaymentEvent


# ────────────────────── Repository Pattern ──────────────────────

class PaymentRepository(ABC):
    """Port outbound : persistance des paiements."""
    
    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        """Sauvegarder (créer ou mettre à jour) un paiement."""
        pass
    
    @abstractmethod
    async def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """Chercher un paiement par ID."""
        pass
    
    @abstractmethod
    async def find_by_booking(self, booking_id: str) -> list[Payment]:
        """Chercher tous les paiements d'une réservation."""
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: PaymentStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """Chercher les paiements par statut."""
        pass
    
    @abstractmethod
    async def delete(self, payment_id: str) -> bool:
        """Soft delete un paiement."""
        pass


# ────────────────────── Event Publisher (Observer Pattern) ──────────────────────

class PaymentEventPublisher(ABC):
    """
    Port outbound : publication d'événements.
    
    Observer Pattern : le publisher notifie tous les subscribers
    (autres services, analytics, audit, etc.)
    """
    
    @abstractmethod
    async def publish(self, event: PaymentEvent) -> None:
        """Publier un événement de paiement."""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: list[PaymentEvent]) -> None:
        """Publier plusieurs événements à la fois."""
        pass


# ────────────────────── External Payment Provider ──────────────────────

class PaymentProvider(ABC):
    """
    Port outbound : communication avec un provider de paiement externe.
    
    Implémentations possibles : Stripe, PayPal, Adyen, etc.
    """
    
    @abstractmethod
    async def process_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str,
        method: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Traiter un paiement auprès du provider.
        
        Retourne :
        {
            "success": bool,
            "transaction_id": str,
            "error_code": str (si échec),
            "error_message": str (si échec),
        }
        """
        pass
    
    @abstractmethod
    async def refund_payment(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
    ) -> dict:
        """
        Rembourser auprès du provider.
        
        Retourne :
        {
            "success": bool,
            "refund_id": str,
            "error_message": str (si échec),
        }
        """
        pass
    
    @abstractmethod
    async def verify_payment(self, transaction_id: str) -> dict:
        """Vérifier l'état d'un paiement auprès du provider."""
        pass


# ────────────────────── System Log (traçabilité) ──────────────────────

class SystemLogPort(ABC):
    """Port outbound : envoi des logs au log-service."""
    
    @abstractmethod
    async def log(
        self,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Envoyer un log système."""
        pass


# ────────────────────── Audit Log (conformité) ──────────────────────

class AuditLogPort(ABC):
    """Port outbound : logs d'audit pour conformité."""
    
    @abstractmethod
    async def log_action(
        self,
        user_id: str,
        action: str,
        entity: str,
        entity_id: str,
        details: Optional[dict] = None,
    ) -> None:
        """Envoyer un log d'audit."""
        pass
