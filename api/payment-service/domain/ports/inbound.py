"""
Ports Inbound — Interfaces exposées par le domaine

📚 Explication Pédagogique :
Les ports inbound sont les "use cases" exposés par le domaine.
Chaque service/adaptateur qui veut faire quelque chose avec les paiements
doit passer par ces interfaces.

Exemple flux :
API HTTP → PaymentInputPort → PaymentService (impl) → DB via outbound port
"""
from abc import ABC, abstractmethod
from typing import Optional

from domain.models.payment import Payment, PaymentStatus, PaymentMethod


class PaymentInputPort(ABC):
    """Port d'entrée : use cases de paiement."""
    
    @abstractmethod
    async def create_payment(
        self,
        booking_id: str,
        amount: float,
        currency: str = "EUR",
        method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        metadata: Optional[dict] = None,
    ) -> Payment:
        """Créer un paiement."""
        pass
    
    @abstractmethod
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Récupérer un paiement par ID."""
        pass
    
    @abstractmethod
    async def get_payments_by_booking(self, booking_id: str) -> list[Payment]:
        """Lister tous les paiements d'une réservation."""
        pass
    
    @abstractmethod
    async def process_payment(self, payment_id: str) -> Payment:
        """Traiter (simuler) le paiement (validation auprès du provider)."""
        pass
    
    @abstractmethod
    async def confirm_payment(self, payment_id: str) -> Payment:
        """Confirmer qu'un paiement est validé."""
        pass
    
    @abstractmethod
    async def cancel_payment(self, payment_id: str) -> Payment:
        """Annuler un paiement."""
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str, refund_amount: Optional[float] = None) -> Payment:
        """Rembourser un paiement (partiellement ou totalement)."""
        pass
    
    @abstractmethod
    async def list_payments(
        self,
        status: Optional[PaymentStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """Lister les paiements avec filtres."""
        pass
