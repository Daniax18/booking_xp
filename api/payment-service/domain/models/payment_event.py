"""
Payment Domain Events — Pattern EVENT

📚 Explication Pédagogique :
Les "Domain Events" sont des faits qui se sont produits dans le domaine.
Ils servent à :
1. Notifier les autres services (booking, log, inventory)
2. Implémenter l'Observer Pattern (observer = autres services)
3. Assurer la traçabilité complète d'un paiement

Exemple : Quand un paiement passe à PAID, on émet un PaymentPaidEvent
qui sera consommé par :
- notification-service (envoyer mail)
- booking-service (marquer réservation comme payée)
- log-service (audit)
- analytics (statistiques)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PaymentEvent:
    """Classe de base pour les événements de paiement."""
    
    payment_id: str
    booking_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Sérialiser l'événement."""
        return {
            "event_type": self.__class__.__name__,
            "payment_id": self.payment_id,
            "booking_id": self.booking_id,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


@dataclass
class PaymentCreatedEvent(PaymentEvent):
    """Événement : Paiement créé."""
    amount: float = 0.0
    currency: str = "EUR"
    method: str = "CREDIT_CARD"


@dataclass
class PaymentProcessingStartedEvent(PaymentEvent):
    """Événement : Paiement en cours de traitement."""
    pass


@dataclass
class PaymentPaidEvent(PaymentEvent):
    """Événement : Paiement confirmé."""
    amount: float = 0.0
    currency: str = "EUR"
    
    def __post_init__(self):
        """Observer Pattern : ce que les subscribers voient."""
        # Les subscribers (autres services) verront cet événement
        pass


@dataclass
class PaymentFailedEvent(PaymentEvent):
    """Événement : Paiement échoué."""
    error_message: str = ""
    error_code: str = ""


@dataclass
class PaymentCancelledEvent(PaymentEvent):
    """Événement : Paiement annulé."""
    reason: str = ""


@dataclass
class PaymentRefundedEvent(PaymentEvent):
    """Événement : Paiement remboursé."""
    refund_amount: float = 0.0
    refund_percentage: float = 0.0
