"""
Payment Domain Model — Entité métier du paiement

📚 Explication Pédagogique :
Le modèle de domaine est l'entité la plus importante.
Il encapsule :
- Les données (id, booking_id, amount, status, etc.)
- La validation métier (enum pour status, vérifications)
- Les comportements métier (peut-on annuler ? peut-on rembourser ?)

⚠️ RÈGLES MÉTIER :
- Un paiement PENDING peut être validé/annulé
- Un paiement PAID ne peut que être remboursé
- Un paiement ne peut jamais revenir à PENDING
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class PaymentStatus(str, Enum):
    """États possibles d'un paiement."""
    PENDING = "PENDING"           # En attente de traitement
    PROCESSING = "PROCESSING"     # En cours de traitement
    PAID = "PAID"                 # Paiement réussi
    FAILED = "FAILED"             # Paiement échoué
    CANCELLED = "CANCELLED"       # Annulé par l'utilisateur
    REFUNDED = "REFUNDED"         # Totalement remboursé


class PaymentMethod(str, Enum):
    """Méthodes de paiement supportées."""
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PAYPAL = "PAYPAL"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOBILE_PAYMENT = "MOBILE_PAYMENT"


@dataclass
class Payment:
    """
    Entité Payment — Le domaine métier du paiement.
    
    📌 Invariants métier (jamais violés) :
    - amount > 0
    - status cohérent avec les transitions autorisées
    - booking_id toujours fourni
    """
    
    # Identifiants & références
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str = field(default="")
    
    # Montant & devise
    amount: float = field(default=0.0)
    currency: str = field(default="EUR")
    
    # État & méthode
    status: PaymentStatus = field(default=PaymentStatus.PENDING)
    method: PaymentMethod = field(default=PaymentMethod.CREDIT_CARD)
    
    # Métadonnées temporelles
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Détails additionnels (optionnels)
    metadata: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    refunded_amount: float = field(default=0.0)
    
    def __post_init__(self):
        """Valider les invariants métier."""
        if not self.booking_id:
            raise ValueError("booking_id est obligatoire")
        if self.amount <= 0:
            raise ValueError("amount doit être > 0")
        if self.refunded_amount < 0:
            raise ValueError("refunded_amount ne peut pas être négatif")
        if self.refunded_amount > self.amount:
            raise ValueError("refunded_amount ne peut pas dépasser amount")
    
    # ────────────────── Transitions d'état ──────────────────
    
    def mark_processing(self) -> None:
        """Passer l'état à PROCESSING."""
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Impossible de passer à PROCESSING depuis {self.status.value}")
        self.status = PaymentStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_paid(self) -> None:
        """Marquer le paiement comme réussi."""
        if self.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise ValueError(f"Impossible de passer à PAID depuis {self.status.value}")
        self.status = PaymentStatus.PAID
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str) -> None:
        """Marquer le paiement comme échoué."""
        if self.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise ValueError(f"Impossible de passer à FAILED depuis {self.status.value}")
        self.status = PaymentStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self) -> None:
        """Annuler le paiement."""
        if self.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise ValueError(f"Impossible d'annuler depuis {self.status.value}")
        self.status = PaymentStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def mark_refunded(self, refund_amount: float) -> None:
        """Rembourser le paiement (partiellement ou totalement)."""
        if self.status != PaymentStatus.PAID:
            raise ValueError(f"Impossible de rembourser un paiement en état {self.status.value}")
        if refund_amount <= 0:
            raise ValueError("refund_amount doit être > 0")
        if refund_amount > (self.amount - self.refunded_amount):
            raise ValueError("Montant de remboursement trop importante")
        
        self.refunded_amount += refund_amount
        if self.refunded_amount >= self.amount:
            self.status = PaymentStatus.REFUNDED
        self.updated_at = datetime.utcnow()
    
    # ────────────────── Vérifications métier ──────────────────
    
    def is_terminal_state(self) -> bool:
        """Vérifier si le paiement est dans un état terminal (ne peut plus changer)."""
        return self.status in [PaymentStatus.PAID, PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.REFUNDED]
    
    def is_pending(self) -> bool:
        """Vérifier si le paiement est en attente."""
        return self.status == PaymentStatus.PENDING
    
    def is_paid(self) -> bool:
        """Vérifier si le paiement est confirmé."""
        return self.status == PaymentStatus.PAID
    
    def can_refund(self) -> bool:
        """Vérifier si le paiement peut être remboursé."""
        return self.status == PaymentStatus.PAID and self.refunded_amount < self.amount
    
    def refund_percentage(self) -> float:
        """Calculated refund percentage."""
        if self.amount == 0:
            return 0.0
        return (self.refunded_amount / self.amount) * 100
    
    def to_dict(self) -> dict:
        """Sérialiser en dictionnaire."""
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "method": self.method.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "refunded_amount": self.refunded_amount,
            "refund_percentage": self.refund_percentage(),
            "metadata": self.metadata,
            "error_message": self.error_message,
        }
