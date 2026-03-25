# Inventory Service

Service de gestion des ressources et de leur disponibilité pour une plateforme e-commerce.

## Architecture

Ce service utilise l'**architecture hexagonale (ports et adaptateurs)** pour une séparation claire des préoccupations :

```
inventory-service/
├── domain/                    # Couche métier (logique pure, indépendante de tout framework)
│   ├── models/               # Entités de domaine (Resource, AvailabilitySlot)
│   ├── repositories/         # Interfaces des repositories
│   ├── services/             # Services métier (logique métier complexe)
│   └── exceptions.py         # Exceptions du domaine
├── application/              # Couche application (orchestration des use cases)
│   ├── use_cases/            # Use cases (CreateResource, GetAvailability, etc.)
│   ├── dtos.py              # Data Transfer Objects (requêtes/réponses API)
│   └── validators.py        # Validateurs des données
└── infrastructure/           # Couche infrastructure (détails techniques)
    └── databases/            # Implémentations des repositories avec SQLAlchemy
```

## Fonctionnalités

### Gestion des Ressources
- Créer une ressource (salle, équipement, véhicule, service)
- Récupérer les détails d'une ressource
- Lister toutes les ressources (avec filtrage par type)
- Mettre à jour une ressource
- Activer/désactiver une ressource

### Gestion de la Disponibilité
- Créer des créneaux de disponibilité
- Vérifier la disponibilité pour une période donnée
- Trouver le prochain créneau disponible
- Marquer des périodes comme indisponibles (maintenance, fermeture, etc.)
- Gérer les quantités disponibles par créneau

## Installation

### Prérequis
- Python 3.9+
- pip

### Setup

1. **Cloner le projet** (ou naviguer dans le répertoire)

```bash
cd api/inventory-service
```

2. **Créer un environnement virtuel**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**

```bash
cp .env.example .env
# Éditer .env selon vos besoins
```

5. **Lancer le service**

```bash
python main.py
```

Le service sera disponible à `http://localhost:8002`

## Documentation de l'API

### Ressources

#### Créer une ressource
```http
POST /resources
Content-Type: application/json

{
  "name": "Salle de réunion A",
  "type": "room",
  "description": "Salle de réunion avec vidéoprojecteur",
  "capacity": 10,
  "location": "Bâtiment A, Étage 2",
  "price": 50.0
}
```

**Réponse (201):**
```json
{
  "id": "uuid",
  "name": "Salle de réunion A",
  "type": "room",
  "capacity": 10,
  "location": "Bâtiment A, Étage 2",
  "price": 50.0,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

#### Récupérer une ressource
```http
GET /resources/{resource_id}
```

#### Lister les ressources
```http
GET /resources
GET /resources?type=room
```

#### Mettre à jour une ressource
```http
PUT /resources/{resource_id}
Content-Type: application/json

{
  "name": "Nouvelle dénomination",
  "price": 75.0
}
```

#### Désactiver/Activer une ressource
```http
POST /resources/{resource_id}/deactivate
POST /resources/{resource_id}/activate
```

### Disponibilité

#### Créer un créneau de disponibilité
```http
POST /resources/{resource_id}/availability
Content-Type: application/json

{
  "resource_id": "uuid",
  "start_time": "2024-01-20T09:00:00",
  "end_time": "2024-01-20T17:00:00",
  "quantity": 2
}
```

#### Vérifier la disponibilité
```http
GET /resources/{resource_id}/availability/check?start_time=2024-01-20T10:00:00&end_time=2024-01-20T12:00:00&quantity=1
```

#### Récupérer les créneaux disponibles
```http
GET /resources/{resource_id}/availability?start_time=2024-01-20T08:00:00&end_time=2024-01-20T18:00:00
```

#### Trouver le prochain créneau disponible
```http
GET /resources/{resource_id}/availability/next-slot?start_time=2024-01-20T10:00:00&duration_minutes=120
```

## Docker

### Lancer avec Docker Compose

```bash
docker-compose up -d inventory-service
```

### Dockerfile

Un Dockerfile est inclus pour containeriser le service.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## Exemples d'utilisation

### Exemple complet

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

# 1. Créer une ressource
resource_data = {
    "name": "Salle 101",
    "type": "room",
    "description": "Salle de réunion",
    "capacity": 20,
    "location": "Building A",
    "price": 100.0
}
response = requests.post(f"{BASE_URL}/resources", json=resource_data)
resource = response.json()
resource_id = resource["id"]
print(f"Ressource créée: {resource_id}")

# 2. Créer des créneaux de disponibilité
start = datetime.now() + timedelta(days=1)
end = start + timedelta(hours=8)

slot_data = {
    "resource_id": resource_id,
    "start_time": start.isoformat(),
    "end_time": end.isoformat(),
    "quantity": 1
}
response = requests.post(
    f"{BASE_URL}/resources/{resource_id}/availability",
    json=slot_data
)
print(f"Créneau créé: {response.json()}")

# 3. Vérifier la disponibilité
check_start = (start + timedelta(hours=1)).isoformat()
check_end = (start + timedelta(hours=3)).isoformat()
response = requests.get(
    f"{BASE_URL}/resources/{resource_id}/availability/check",
    params={
        "start_time": check_start,
        "end_time": check_end,
        "quantity": 1
    }
)
print(f"Disponibilité: {response.json()}")
```

## Tests

Pour exécuter les tests :

```bash
pytest tests/
```

## Intégration avec les autres services

### Booking Service
Le Booking Service utilisera ce service pour vérifier la disponibilité des ressources avant de créer une réservation.

### Auth Service
L'Auth Service fournira l'authentification et les autorisations pour accéder aux endpoints.

### Payment Service
Après un paiement réussi, le Booking Service met à jour la disponibilité via ce service.

## Bonnes pratiques

1. **Validation des données** : Toutes les entrées sont validées
2. **Gestion des erreurs** : Exceptions claires et documentées
3. **Logging** : Tous les événements importants sont loggés
4. **Séparation des préoccupations** : Architecture hexagonale
5. **Tests** : Code testable et maintenable
6. **Documentation** : API bien documentée avec des exemples

## Améliorations futures

- [ ] Ajouter des tests unitaires et d'intégrité
- [ ] Implémenter la mise en cache (Redis)
- [ ] Ajouter la pagination pour les listes
- [ ] Implémenter une authentification JWT
- [ ] Ajouter des événements de domaine pour les réservations
- [ ] Implémenter les patterns SAGA pour l'orchestration distribuée
- [ ] Ajouter des métriques Prometheus
- [ ] Implémenter un circuit breaker pour la Communication inter-services

## Contribution

Pour contribuer au projet, veuillez :
1. Créer une branche pour votre feature
2. Committer vos changements
3. Pusher votre branche
4. Créer une Pull Request

## Licence

MIT
