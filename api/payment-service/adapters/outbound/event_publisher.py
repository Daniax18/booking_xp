"""
Event Publisher — Pattern OBSERVER

📚 Explication Pédagogique :
Le event publisher implémente le pattern Observer.

Quand on publie un événement (ex: PaymentPaidEvent),
tous les subscribers (autres services) sont notifiés :
- booking-service : marquer la réservation comme payée
- notification-service : envoyer un email
- analytics : statistiques
- log-service : audit

Implémentations possibles :
- InMemory : pour les tests
- RabbitMQ : pour la production
- Kafka : pour le streaming temps réel
"""
from typing import Callable, Optional
from domain.models.payment_event import PaymentEvent
from domain.ports.outbound import PaymentEventPublisher


class InMemoryEventPublisher(PaymentEventPublisher):
    """
    Publisher en mémoire pour développement et tests.
    
    Stocke les événements et les notifie aux subscribers.
    """
    
    def __init__(self):
        """Initialiser le registry de subscribers."""
        self._subscribers: dict[str, list[Callable]] = {}
        self._events: list[PaymentEvent] = []
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """S'inscrire pour recevoir un type d'événement."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def publish(self, event: PaymentEvent) -> None:
        """Publier un événement et notifier les subscribers."""
        self._events.append(event)
        
        event_type = event.__class__.__name__
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                # Appeler les callbacks (les autres services)
                # En production, ce seraient des appels HTTP/gRPC
                await callback(event) if callable(callback) else None
    
    async def publish_batch(self, events: list[PaymentEvent]) -> None:
        """Publier plusieurs événements à la fois."""
        for event in events:
            await self.publish(event)
    
    def get_events(self) -> list[PaymentEvent]:
        """Récupérer les événements publiés (pour les tests)."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Vider les événements (pour les tests)."""
        self._events.clear()
