"""
Mock Payment Provider — Adaptateur pour provider externe

📚 Explication Pédagogique :
Le payment provider est une abstraction pour discuter avec
un vrai provider de paiement (Stripe, PayPal, Adyen, etc.).

Pour le développement, on utilise MockPaymentProvider.
En production, on utiliserait StripePaymentProvider, etc.
"""
from typing import Optional
from domain.ports.outbound import PaymentProvider
import asyncio
import random


class MockPaymentProvider(PaymentProvider):
    """
    Mock provider pour développement et tests.
    
    Simule les appels au provider sans faire de vrais paiements.
    """
    
    def __init__(self, success_rate: float = 0.8):
        """
        Initialiser le mock.
        
        Args:
            success_rate: % de paiements réussis (entre 0 et 1)
        """
        self.success_rate = success_rate
    
    async def process_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str,
        method: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Traiter un paiement (simulation).
        
        Retourne un dict avec succès ou erreur.
        """
        # Simuler un appel réseau (délai)
        await asyncio.sleep(0.5)
        
        # Décider aléatoirement du succès
        if random.random() < self.success_rate:
            # Succès
            return {
                "success": True,
                "transaction_id": f"txn_{payment_id}_{random.randint(1000, 9999)}",
                "method": method,
                "amount": amount,
            }
        else:
            # Échec
            error_codes = ["INSUFFICIENT_FUNDS", "CARD_DECLINED", "EXPIRED_CARD"]
            return {
                "success": False,
                "error_code": random.choice(error_codes),
                "error_message": "Paiement refusé par le provider",
            }
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
    ) -> dict:
        """Rembourser un paiement."""
        await asyncio.sleep(0.3)
        
        return {
            "success": True,
            "refund_id": f"refund_{transaction_id}",
            "amount": amount,
        }
    
    async def verify_payment(self, transaction_id: str) -> dict:
        """Vérifier l'état d'un paiement."""
        await asyncio.sleep(0.2)
        
        return {
            "transaction_id": transaction_id,
            "status": "PAID",
            "verified": True,
        }


class StripePaymentProvider(PaymentProvider):
    """
    Adaptateur réel pour Stripe.
    
    À implémenter pour la production avec la lib stripe.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def process_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str,
        method: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Traiter un paiement avec Stripe."""
        # TODO : implémenter avec stripe.com
        raise NotImplementedError("Stripe provider not implemented yet")
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
    ) -> dict:
        """Rembourser avec Stripe."""
        # TODO : implémenter
        raise NotImplementedError("Stripe refund not implemented yet")
    
    async def verify_payment(self, transaction_id: str) -> dict:
        """Vérifier avec Stripe."""
        # TODO : implémenter
        raise NotImplementedError("Stripe verify not implemented yet")
