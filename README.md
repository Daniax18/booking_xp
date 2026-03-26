# ðŸ“‹ Booking XP â€” Plateforme de RÃ©servation

> SystÃ¨me de gestion de rÃ©servations (restaurant / hÃ´tel / salle) en microservices
> Architecture Hexagonale â€¢ Python / FastAPI â€¢ PostgreSQL â€¢ Docker

## ðŸ—ï¸ Architecture

Le projet suit une **architecture hexagonale** (Ports & Adapters) avec le pattern **Database per Service**.

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     API Gateway                         â”‚
â”‚              (reverse proxy / load balancer)             â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Auth  â”‚ Booking  â”‚ Payment  â”‚ Inventory â”‚     Log      â”‚
â”‚ :8001  â”‚  :8003   â”‚  :8004   â”‚   :8002   â”‚    :8005     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ auth   â”‚ booking  â”‚ payment  â”‚ inventory â”‚    log       â”‚
â”‚  _db   â”‚   _db    â”‚   _db    â”‚    _db    â”‚    _db       â”‚
â”‚ :5431  â”‚  :5433   â”‚  :5434   â”‚   :5432   â”‚   :5435      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Structure d'un service (Hexagonal)
```
service/
â”œâ”€â”€ domain/              # ðŸ§  CÅ“ur mÃ©tier (indÃ©pendant)
â”‚   â”œâ”€â”€ models/          # EntitÃ©s du domaine
â”‚   â”œâ”€â”€ ports/           # Interfaces (inbound/outbound)
â”‚   â””â”€â”€ services/        # Logique mÃ©tier
â”œâ”€â”€ adapters/            # ðŸ”Œ Connexion au monde extÃ©rieur
â”‚   â”œâ”€â”€ inbound/         # API REST (routes, schÃ©mas)
â”‚   â””â”€â”€ outbound/        # Repositories (PostgreSQL)
â”œâ”€â”€ infrastructure/      # âš™ï¸ Configuration, DB, middleware
â”œâ”€â”€ tests/               # âœ… Tests unitaires & intÃ©gration
â”œâ”€â”€ Dockerfile           # ðŸ³ Image Docker
â””â”€â”€ main.py              # ðŸš€ Point d'entrÃ©e
```

## ðŸ‘¥ Ã‰quipe & Tickets (Sprint 2)

| Ticket | Service | Responsable | Status |
|--------|---------|-------------|--------|
| RX-1 | Auth Service | ANDRIANANDRASANA Midera Dania | ðŸŸ¡ En cours |
| RX-2 | Inventory Service | Daddy Luciano RAVALISON | ðŸ”µ Ã€ faire |
| RX-3 | Booking Service | Gaelle Robsomanitrandrasana | ✅ Terminé |
| RX-4 | Payment Service | Manoa Robel | ðŸ”µ Ã€ faire |
| RX-5 | Log Service | mccibs25273 (El Nadje) | ðŸŸ¡ En cours |
| RX-6 | Config Git & Structure | ANDRIANANDRASANA M. Dania | âœ… TerminÃ© |
| RX-7 | PrÃ©sentation PPT | Non assignÃ© | ðŸ”µ Ã€ faire |
| RX-8 | Pipeline CI-CD | mccibs25273 (El Nadje) | ðŸ”µ Ã€ faire |

## ðŸš€ DÃ©marrage rapide

### PrÃ©requis
- Docker & Docker Compose
- Python 3.12+
- Git

### Lancer tous les services
```bash
docker compose up -d --build
```

### Lancer un service spÃ©cifique (dev)
```bash
cd api/log-service
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8005
```

### ExÃ©cuter les tests
```bash
cd api/log-service
pytest tests/ -v --cov=domain
```

## ðŸ“š Documentation API

Chaque service expose sa documentation Swagger :
- Auth : http://localhost:8001/docs
- Inventory : http://localhost:8002/docs
- Booking : http://localhost:8003/docs
- Payment : http://localhost:8004/docs
- **Log** : http://localhost:8005/docs

## ðŸ”„ CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci-cd.yml`) exÃ©cute :
1. **Lint** â†’ flake8 (style), mypy (types)
2. **Test** â†’ pytest avec couverture de code
3. **Build** â†’ Images Docker (GitHub Container Registry)
4. **Deploy** â†’ Staging (develop) / Production (main) avec Blue/Green

## ðŸ”— Communication inter-services

- **REST API** : communication synchrone entre services
- **X-Correlation-ID** : header HTTP propagÃ© pour traÃ§abilitÃ©
- **Log Service** : centralisation des logs via `POST /api/v1/system-logs`
- **Health Checks** : `GET /api/v1/health` sur chaque service

## ðŸ“Š ModÃ¨le de DonnÃ©es

### Enums
- `ResourceType` : HOTEL_ROOM, RESTAURANT_TABLE, VENUE
- `BookingStatus` : PENDING, CONFIRMED, CANCELLED
- `PaymentStatus` : PENDING, PAID, FAILED

### EntitÃ©s principales
- `User`, `Resource`, `Booking`, `Payment`, `AvailabilitySlot`
- `SystemLog`, `AuditLog` (log-service)

## ðŸŒ¿ Branches Git

- `main` â€” Production stable
- `develop` â€” IntÃ©gration des features
- `feature/rx1-authentification` â€” Auth (Dania)
- `feature/rx5-log-service` â€” Log + CI/CD (El Nadje)

## Booking Service Presentation

Le `booking-service` est maintenant implemente en architecture hexagonale dans `api/booking-service`.

### Responsabilites metier
- Creer une reservation pour un restaurant, une chambre d'hotel ou une salle.
- Verifier la disponibilite locale en evitant les chevauchements de creneaux.
- Calculer ou accepter le prix total de la reservation.
- Orchestrer une Saga `booking + payment`.
- Preparer la communication avec `inventory-service` et `payment-service`.
- Publier des logs structures et des evenements metier.

### Structure interne
```text
api/booking-service/
├── domain/
│   ├── models/           # Entite Booking + enums metier
│   ├── ports/            # Interfaces inbound / outbound
│   ├── services/         # BookingService (cas d'usage)
│   ├── pricing.py        # Strategy pattern pour le calcul de prix
│   └── specifications.py # Specification pattern pour disponibilite / regles
├── adapters/
│   ├── inbound/          # Routes FastAPI + schemas Pydantic
│   └── outbound/         # Repository SQLAlchemy + clients HTTP + event publisher
├── infrastructure/       # Config, DB async, middleware, logging structure
├── tests/                # Tests unitaires, integration, contrat
├── Dockerfile
└── main.py
```

### Design patterns utilises
- `Repository` : isolation de la persistence via `PostgresBookingRepository`.
- `Strategy` : calcul de prix selon le type de ressource (`HOTEL_ROOM`, `RESTAURANT_TABLE`, `VENUE`).
- `Specification` : validation des creneaux, du nombre de personnes et des conflits de disponibilite.
- `Saga` : orchestration de la reservation distribuee avec compensation si le paiement echoue.

### Disponibilite et regles metier
- Une reservation ne peut pas avoir une `end_time` avant `start_time`.
- `party_size` doit etre strictement positif.
- Deux reservations actives ne peuvent pas se chevaucher pour la meme ressource.
- Le service peut fonctionner en mode `stub` pour `inventory` et `payment` tant que les autres equipes n'ont pas termine.

### Communication inter-services preparee

#### Appels REST sortants
- `POST /api/v1/inventory/internal/availability/check`
- `POST /api/v1/inventory/internal/reservations/hold`
- `POST /api/v1/inventory/internal/reservations/release`
- `POST /api/v1/payments/internal/transactions`
- `POST /api/v1/payments/internal/transactions/cancel`

#### Evenements publies
- `booking.created`
- `booking.confirmed`
- `booking.cancelled`
- `booking.payment_failed`

#### Evenements consommes
- `payment.status_changed`
- `inventory.status_changed`

### Observabilite
- Middleware `X-Correlation-ID` pour tracer une requete entre plusieurs services.
- Logs structures pour les appels API, les appels d'integration et les evenements.
- Endpoint de health check : `GET /api/v1/bookings/health`
- Endpoint de documentation des contrats : `GET /api/v1/bookings/contracts/communication`

### Endpoints principaux
- `POST /api/v1/bookings`
- `GET /api/v1/bookings?user_id=...`
- `GET /api/v1/bookings/{booking_id}`
- `POST /api/v1/bookings/{booking_id}/cancel`
- `POST /api/v1/bookings/events/payment`
- `POST /api/v1/bookings/events/inventory`

### Tests ajoutes
- Tests unitaires du domaine : regles metier, disponibilite, Saga.
- Tests d'integration : repository SQLAlchemy.
- Tests de contrat : format des appels HTTP vers `inventory` et `payment`.

