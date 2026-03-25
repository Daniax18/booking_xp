# 📋 Booking XP — Plateforme de Réservation

> Système de gestion de réservations (restaurant / hôtel / salle) en microservices
> Architecture Hexagonale • Python / FastAPI • PostgreSQL • Docker

## 🏗️ Architecture

Le projet suit une **architecture hexagonale** (Ports & Adapters) avec le pattern **Database per Service**.

```
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                         │
│              (reverse proxy / load balancer)             │
├────────┬──────────┬──────────┬───────────┬──────────────┤
│  Auth  │ Booking  │ Payment  │ Inventory │     Log      │
│ :8001  │  :8003   │  :8004   │   :8002   │    :8005     │
├────────┼──────────┼──────────┼───────────┼──────────────┤
│ auth   │ booking  │ payment  │ inventory │    log       │
│  _db   │   _db    │   _db    │    _db    │    _db       │
│ :5431  │  :5433   │  :5434   │   :5432   │   :5435      │
└────────┴──────────┴──────────┴───────────┴──────────────┘
```

### Structure d'un service (Hexagonal)
```
service/
├── domain/              # 🧠 Cœur métier (indépendant)
│   ├── models/          # Entités du domaine
│   ├── ports/           # Interfaces (inbound/outbound)
│   └── services/        # Logique métier
├── adapters/            # 🔌 Connexion au monde extérieur
│   ├── inbound/         # API REST (routes, schémas)
│   └── outbound/        # Repositories (PostgreSQL)
├── infrastructure/      # ⚙️ Configuration, DB, middleware
├── tests/               # ✅ Tests unitaires & intégration
├── Dockerfile           # 🐳 Image Docker
└── main.py              # 🚀 Point d'entrée
```

## 👥 Équipe & Tickets (Sprint 2)

| Ticket | Service | Responsable | Status |
|--------|---------|-------------|--------|
| RX-1 | Auth Service | ANDRIANANDRASANA Midera Dania | 🟡 En cours |
| RX-2 | Inventory Service | Daddy Luciano RAVALISON | 🔵 À faire |
| RX-3 | Booking Service | Gaelle Robsomanitrandrasana | 🔵 À faire |
| RX-4 | Payment Service | Manoa Robel | 🔵 À faire |
| RX-5 | Log Service | mccibs25273 (El Nadje) | 🟡 En cours |
| RX-6 | Config Git & Structure | ANDRIANANDRASANA M. Dania | ✅ Terminé |
| RX-7 | Présentation PPT | Non assigné | 🔵 À faire |
| RX-8 | Pipeline CI-CD | mccibs25273 (El Nadje) | 🔵 À faire |

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Python 3.12+
- Git

### Lancer tous les services
```bash
docker compose up -d --build
```

### Lancer un service spécifique (dev)
```bash
cd api/log-service
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8005
```

### Exécuter les tests
```bash
cd api/log-service
pytest tests/ -v --cov=domain
```

## 📚 Documentation API

Chaque service expose sa documentation Swagger :
- Auth : http://localhost:8001/docs
- Inventory : http://localhost:8002/docs
- Booking : http://localhost:8003/docs
- Payment : http://localhost:8004/docs
- **Log** : http://localhost:8005/docs

## 🔄 CI/CD

Le pipeline GitHub Actions (`.github/workflows/ci-cd.yml`) exécute :
1. **Lint** → flake8 (style), mypy (types)
2. **Test** → pytest avec couverture de code
3. **Build** → Images Docker (GitHub Container Registry)
4. **Deploy** → Staging (develop) / Production (main) avec Blue/Green

## 🔗 Communication inter-services

- **REST API** : communication synchrone entre services
- **X-Correlation-ID** : header HTTP propagé pour traçabilité
- **Log Service** : centralisation des logs via `POST /api/v1/system-logs`
- **Health Checks** : `GET /api/v1/health` sur chaque service

## 📊 Modèle de Données

### Enums
- `ResourceType` : HOTEL_ROOM, RESTAURANT_TABLE, VENUE
- `BookingStatus` : PENDING, CONFIRMED, CANCELLED
- `PaymentStatus` : PENDING, PAID, FAILED

### Entités principales
- `User`, `Resource`, `Booking`, `Payment`, `AvailabilitySlot`
- `SystemLog`, `AuditLog` (log-service)

## 🌿 Branches Git

- `main` — Production stable
- `develop` — Intégration des features
- `feature/rx1-authentification` — Auth (Dania)
- `feature/rx5-log-service` — Log + CI/CD (El Nadje)
