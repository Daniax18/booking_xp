# Booking XP - Plateforme de reservation

Systeme de gestion de reservations (restaurant / hotel / salle) en microservices.
Architecture hexagonale, Python / FastAPI, PostgreSQL et Docker.

## Architecture

Le projet suit une architecture hexagonale (Ports and Adapters) avec le pattern Database per Service.
Chaque microservice possede sa propre base PostgreSQL.

Services exposes:
- auth-service: `:8001`
- inventory-service: `:8002`
- booking-service: `:8003`
- payment-service: `:8004`
- log-service: `:8005`

Bases de donnees:
- auth-db: `:5431`
- inventory-db: `:5432`
- booking-db: `:5433`
- payment-db: `:5434`
- log-db: `:5435`

## Structure d'un service

```text
service/
  domain/
    models/
    ports/
    services/
  adapters/
    inbound/
    outbound/
  infrastructure/
  tests/
  Dockerfile
  main.py
```

## Equipe et tickets

- RX-1 Authentification: auth-service
- RX-2 Ressources et disponibilites: inventory-service
- RX-3 Reservations: booking-service
- RX-4 Paiement: payment-service
- RX-5 Observabilite: log-service

## Demarrage

Lancer toute la plateforme:

```bash
docker compose up -d --build
```

Verifier la configuration Docker Compose:

```bash
docker compose config
```

## Booking service

Le booking-service implemente l'architecture hexagonale complete.
Il gere:
- la creation de reservation
- la verification des conflits temporels
- la verification de disponibilite avec inventory-service
- la saga reservation + paiement
- les audit logs, system logs et evenements

Patterns utilises:
- Repository
- Strategy
- Specification
- Saga

Observabilite:
- health check
- logs structures
- correlation id via `X-Correlation-ID`

Tests booking:
- unitaires domaine
- integration repository
- contrats interservices
- routes et schemas

## CI/CD

Le workflow GitHub Actions se trouve dans `.github/workflows/ci-cd.yml`.
Il lance le lint, les tests, le build Docker et prepare le deploiement staging / production.

## Remarques

- inventory-service et payment-service sont integres via HTTP.
- Les logs d'acces HTTP sont structures localement.
- Les logs metier et techniques du booking-service sont envoyes vers log-service.
