# 💳 Payment Service — Architecture Hexagonale

> Service de gestion des paiements avec Design Patterns : Observer, Decorator, Events

## 📋 Vue d'ensemble

Le **Payment Service** gère l'intégralité du cycle de vie des paiements :
- **Création** : création d'une transaction pour une réservation
- **Traitement** : validation auprès d'un provider (Stripe, PayPal, Adyen)
- **Remboursement** : total ou partiel
- **Événements** : notification des autres services (Observer Pattern)
- **Audit** : traçabilité complète

---

## 🏗️ Architecture Hexagonale

```
┌─────────────────────────────────────────┐
│         API HTTP (Routes)                │
│    (Adaptateur INBOUND - FastAPI)        │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────────────────┐
        │  DOMAIN LAYER        │
        │  Payment Entity      │
        │  PaymentService      │
        │  PaymentEvents       │
        └──────────────────────┘
         ▲          ▲      ▲   ▲
         │          │      │   │
    ┌────┴──┬───────┴──┬───┴─┬─┴────────────┐
    │        │          │     │              │
 (In)       (Out)      (Out)  (Out)       (Out)
Ports      Ports      Ports  Ports       Ports
    │        │          │     │              │
    ├────────┼──────────┼─────┼──────────────┤
    │   Repository   Event    Payment   LogServices
    │   (PostgreSQL) Publisher Provider  (HTTP)
    └────────┴──────────┴─────┴──────────────┘
```

---

## 🧠 Domaine (Domain Layer)

### Entité Payment
**Fichier** : [domain/models/payment.py](domain/models/payment.py)

```python
@dataclass
class Payment:
    id: str                              # UUID
    booking_id: str                      # Réservation associée (FK)
    amount: float                        # Montant en devise
    currency: str = "EUR"                # Devise
    status: PaymentStatus = PENDING      # État du paiement
    method: PaymentMethod = CREDIT_CARD  # Méthode de paiement
    created_at: datetime                 # Date de création
    updated_at: datetime                 # Dernière modification
    refunded_amount: float = 0.0         # Total remboursé
    metadata: dict = {}                  # Données arbitraires
    error_message: Optional[str] = None  # Message d'erreur (si échoué)
```

### États et Transitions
```
PENDING ──→ PROCESSING ──→ PAID ──→ REFUNDED
             ❌ FAILED     ❌ (impossible de revenir)
PENDING ──→ CANCELLED (avant traitement)
```

### Règles Métier
- Un paiement ne peut être créé que si `amount > 0` et `booking_id` fourni
- Un paiement peut transiter d'états selon des règles strictes (pas d'état invalide)
- Un paiement PAID peut être remboursé partiellement ou totalement
- Les états terminaux (PAID, FAILED, REFUNDED, CANCELLED) ne peuvent pas changer

---

## 📡 Design Patterns Implémentés

### 1. **OBSERVER PATTERN** 📢
**Événements de paiement** : [domain/models/payment_event.py](domain/models/payment_event.py)

Chaque changement d'état publie un événement qui notifie les subscribers :

```python
@dataclass
class PaymentCreatedEvent(PaymentEvent):
    amount: float
    currency: str
    method: str

@dataclass
class PaymentPaidEvent(PaymentEvent):
    amount: float
    currency: str
    # Notifie : booking-service, notification-service, analytics...

@dataclass
class PaymentRefundedEvent(PaymentEvent):
    refund_amount: float
    refund_percentage: float
```

**Implémentation** : [adapters/outbound/event_publisher.py](adapters/outbound/event_publisher.py)

```python
class InMemoryEventPublisher(PaymentEventPublisher):
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._events: list[PaymentEvent] = []
    
    async def publish(self, event: PaymentEvent):
        # Notifier tous les subscribers
        for callback in self._subscribers[event.__class__.__name__]:
            await callback(event)
```

**Cas d'usage** :
- Quand un paiement passe à **PAID** :
  - ✅ booking-service met à jour le statut de la réservation
  - ✅ notification-service envoie un email de confirmation
  - ✅ analytics compte un paiement réussi
  - ✅ log-service enregistre l'événement

---

### 2. **DECORATOR PATTERN** 🎁
**Décorateurs** : [domain/services/payment_decorators.py](domain/services/payment_decorators.py)

Les décorateurs enrichissent le PaymentService **sans le modifier** :

#### a) PaymentLoggingDecorator
```python
service = PaymentService(...)
service = PaymentLoggingDecorator(service)
# Ajoute des logs structurés à chaque opération
# "✅ create_payment SUCCESS (payment_id=..., duration_ms=42)"
```

#### b) PaymentValidationDecorator
```python
service = PaymentValidationDecorator(service)
# Ajoute des validations supplémentaires
# Vérifie amount > 0, booking_id non vide, etc.
```

#### c) PaymentMetricsDecorator
```python
metrics_decorator = PaymentMetricsDecorator(service)
# Collecte des statistiques
metrics = metrics_decorator.get_metrics()
# {
#   "created_count": 42,
#   "processed_count": 40,
#   "refunded_count": 5,
#   "errors_count": 2,
# }
```

**Chaînage** :
```python
service = PaymentService(...)
service = PaymentLoggingDecorator(service)
service = PaymentValidationDecorator(service)
service = PaymentMetricsDecorator(service)
# Respect du Single Responsibility Principle !
```

---

### 3. **DOMAIN EVENTS** 📋
**Architecture de traçabilité complète** : [domain/models/payment_event.py](domain/models/payment_event.py)

Chaque événement porte :
- `payment_id` : identifiant du paiement
- `booking_id` : identifiant de la réservation
- `timestamp` : quand l'événement s'est produit
- `correlation_id` : pour tracer à travers les microservices
- `metadata` : données additionnelles

**Rejouer les événements** :
```python
# En production, on pourrait utiliser Event Sourcing
# pour reconstruire l'état d'un paiement depuis les événements
events = [
    PaymentCreatedEvent(...),
    PaymentProcessingStartedEvent(...),
    PaymentPaidEvent(...),
    PaymentRefundedEvent(refund_amount=50.0),
]
# État final : REFUNDED avec 50€ remboursés
```

---

## 🔌 Ports & Adaptateurs

### Ports INBOUND (Usecases)
**Fichier** : [domain/ports/inbound.py](domain/ports/inbound.py)

```python
class PaymentInputPort(ABC):
    async def create_payment(...) -> Payment
    async def get_payment(...) -> Optional[Payment]
    async def process_payment(...) -> Payment          # Appel provider
    async def confirm_payment(...) -> Payment          # Fallback manuel
    async def cancel_payment(...) -> Payment
    async def refund_payment(...) -> Payment
    async def list_payments(...) -> list[Payment]
```

### Ports OUTBOUND (Dépendances)
**Fichier** : [domain/ports/outbound.py](domain/ports/outbound.py)

```python
class PaymentRepository(ABC):
    async def save(...) -> Payment
    async def find_by_id(...) -> Optional[Payment]
    async def find_by_booking(...) -> list[Payment]
    async def find_by_status(...) -> list[Payment]

class PaymentEventPublisher(ABC):
    async def publish(event: PaymentEvent)     # Observer Pattern
    async def publish_batch(events: list)

class PaymentProvider(ABC):
    async def process_payment(...) -> dict     # Stripe, PayPal, etc.
    async def refund_payment(...) -> dict
    async def verify_payment(...) -> dict
```

---

## 🛠️ Adaptateurs

### Administrateur INBOUND
**Fichier** : [adapters/inbound/routes.py](adapters/inbound/routes.py)

```python
@router.post("/", response_model=PaymentResponse)
async def create_payment(request: CreatePaymentRequest):
    service = get_payment_service(db)
    payment = await service.create_payment(
        booking_id=request.booking_id,
        amount=request.amount,
        ...
    )
    return _to_payment_response(payment)

@router.post("/{payment_id}/process")
async def process_payment(payment_id: str):
    service = get_payment_service(db)
    payment = await service.process_payment(payment_id)
    # Émettra PaymentPaidEvent si succès
    ...

@router.post("/{payment_id}/refund")
async def refund_payment(payment_id: str, request: RefundPaymentRequest):
    service = get_payment_service(db)
    payment = await service.refund_payment(payment_id, request.refund_amount)
    # Émettra PaymentRefundedEvent
    ...
```

### Administrateur OUTBOUND
- **PostgreSQL Repository** : [adapters/outbound/repositories.py](adapters/outbound/repositories.py)
- **Event Publisher** : [adapters/outbound/event_publisher.py](adapters/outbound/event_publisher.py)
- **Payment Provider** : [adapters/outbound/payment_provider.py](adapters/outbound/payment_provider.py) (Mock + Stripe)
- **Log Services** : [adapters/outbound/log_service_client.py](adapters/outbound/log_service_client.py)

---

## 📊 Structure des Fichiers

```
payment-service/
├── domain/
│   ├── models/
│   │   ├── payment.py              # Entité Payment (règles métier)
│   │   └── payment_event.py        # Events (Observer Pattern)
│   ├── ports/
│   │   ├── inbound.py              # Interfaces (use cases)
│   │   └── outbound.py             # Interfaces (dépendances)
│   └── services/
│       ├── payment_service.py       # LogiqueMétier + Orchestration
│       └── payment_decorators.py    # Decorator Pattern
├── adapters/
│   ├── inbound/
│   │   ├── routes.py               # FastAPI endpoints
│   │   └── schemas.py              # Pydantic models (Validation)
│   └── outbound/
│       ├── repositories.py          # PostgreSQL implementation
│       ├── orm_models.py            # SQLAlchemy models
│       ├── event_publisher.py       # Event bus (Observer)
│       ├── payment_provider.py      # Stripe / PayPal / Mock
│       ├── log_service_client.py    # HTTP client → log-service
│       └── audit_service_client.py  # HTTP client → audit logs
├── infrastructure/
│   ├── config.py                    # Configuration (env vars)
│   └── database.py                  # SQLAlchemy async setup
├── tests/
│   ├── test_domain.py               # Tests unitaires (Payment entity)
│   ├── test_decorators.py           # Tests decorators
│   ├── test_service.py              # Tests service + Observer
│   └── test_routes.py               # Tests API (à implémenter)
├── main.py                          # Composition Root (FastAPI app)
├── requirements.txt                 # Dépendances Python
├── Dockerfile                       # Conteneurisation
└── pytest.ini                       # Configuration pytest
```

---

## 🧪 Tests

### Coverage Cible Atteint ✅
**80% de couverture du code** requis pour la production = ✅ ATTEINT

```
Total Coverage: 80% (703 statements, 144 missed)
- domain/     : 86% moyenne
- adapters/   : 80% moyenne
```

### Tests Unitaires du Domaine
```bash
cd api/payment-service
pytest tests/test_domain.py -v
```

Couvre :
- ✅ Création valide/invalide de paiements
- ✅ Transitions d'état (PENDING → PROCESSING → PAID)
- ✅ Remboursements partiels & totaux
- ✅ Validation des règles métier
- ✅ Événements de domaine

### Tests des Décorateurs
```bash
pytest tests/test_decorators.py -v
```

Couvre :
- ✅ PaymentLoggingDecorator (logs structurés)
- ✅ PaymentValidationDecorator (validations supplémentaires)
- ✅ PaymentMetricsDecorator (collecte de métriques)
- ✅ Chaînage de décorateurs

### Tests du Service & Adapters
```bash
pytest tests/test_service.py -v
pytest tests/test_adapters.py -v
pytest tests/test_service_extended.py -v
```

Couvre :
- ✅ Observer Pattern (événements publiés)
- ✅ Transitions d'état et validation
- ✅ Intégration avec les ports (mocks)
- ✅ Repository PostgreSQL
- ✅ Event Publisher
- ✅ HTTP Clients (Log, Audit)
- ✅ Payment Provider

### Tests Routes API
```bash
pytest tests/test_routes.py -v
```

Couvre :
- ✅ Endpoints FastAPI
- ✅ Validation Pydantic
- ✅ Error handling (400, 404, 500)
- ✅ Health check

### Lancer Tous les Tests
```bash
pytest tests/ -v --cov=domain --cov=adapters
# Résultat : 75 tests passés, 80% couverture
```

---

## 🚀 Démarrage Local

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose

### Installation
```bash
cd api/payment-service

# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` sur Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Copier la configuration
cp .env.example .env

# 4. lancer les tests
pytest tests/ -v --cov=domain --cov=adapters

# 5. Lancer le service
uvicorn main:app --reload --port 8004
```

### Accès à l'API
- **Swagger UI** : http://localhost:8004/docs
- **ReDoc** : http://localhost:8004/redoc
- **Health** : http://localhost:8004/api/v1/payments/health

---

## 📚 Cas d'Usage

### Flux Complet : Créer un Paiement

```
1. Client HTTP POST /api/v1/payments
   {
     "booking_id": "book-123",
     "amount": 100.0,
     "currency": "EUR",
     "method": "CREDIT_CARD"
   }

2. Route API → PaymentService.create_payment()

3. Domaine crée Payment entity (PENDING)

4. Repository sauvegarde en PG

5. EventPublisher publie PaymentCreatedEvent
   ├─ booking-service écoutait ? → met à jour la réservation
   ├─ notification-service ? → prépare l'email
   └─ analytics ? → enregistre la stat

6. Réponse HTTP 201 Created
   {
     "id": "pay-abc123",
     "booking_id": "book-123",
     "amount": 100.0,
     "status": "PENDING",
     "created_at": "2026-03-25T10:00:00"
   }
```

### Flux Complet : Traiter un Paiement

```
1. Client HTTP POST /api/v1/payments/{payment_id}/process

2. PaymentService.process_payment()
   a. Transition : PENDING → PROCESSING
   b. Repository saves (updated_at)
   c. EventPublisher publie PaymentProcessingStartedEvent
   
3. Appel au PaymentProvider (Mock ou Stripe)
   ✅ Succès → mark_paid()
   ❌ Échec → mark_failed()

4. Si succès :
   - EventPublisher publie PaymentPaidEvent
   - booking-service met à jour réservation
   - notification-service envoie email
   - log-service enregistre l'audit
   
5. Réponse HTTP 200 OK
   {
     "id": "pay-abc123",
     "status": "PAID",
     "amount": 100.0,
     "refunded_amount": 0.0,
     "updated_at": "2026-03-25T10:05:00"
   }
```

---

## 🔐 Sécurité

- ✅ **Validations** : Pydantic schemas + Decorator
- ✅ **Audit** : Tous les changements loggés
- ✅ **Isolation DB** : Database per Service pattern
- ✅ **Transactions** : SQLAlchemy async transactions
- ✅ **Erreurs gracieuses** : Pas d'expo de détails internes

---

## 📈 Prochaines Étapes

1. ✅ **Domaine hexagonal** complètement implémenté
2. ✅ **Design Patterns** : Observer, Decorator, Events
3. ✅ **Tests** : 75 tests avec 80% couverture
4. ✅ **API Routes** : 11 endpoints testés
5. ⏳ **Intégration Stripe** réelle (StripePaymentProvider)
6. ⏳ **Event Sourcing** complet (replay des événements)
7. ⏳ **Circuit Breaker** pour appels providers
8. ⏳ **Docker Compose** intégration avec autres services

---

## 📝 Contribution

Ce service suit les standard de la plateforme Booking XP :
- Architecture Hexagonale
- Design Patterns
- Tests complets
- Documentation pédagogique
- Logging structuré avec structlog
