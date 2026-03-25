# 🧪 GUIDE COMPLET DES TESTS - Inventory Service

## 🎯 3 FAÇONS DE TESTER

### 1️⃣ **SANS CODE** - Interface Web (Swagger/ReDoc)
### 2️⃣ **SIMPLE** - Avec curl dans le terminal
### 3️⃣ **PROFESSIONNEL** - Tests unitaires avec pytest

---

## 1️⃣ TESTER AVEC SWAGGER (La plus facile!)

### ✅ Démarrer le service
```bash
python main.py
```

### ✅ Accéder à Swagger
```
http://localhost:8002/docs
```

### ✅ Tester directement dans le navigateur

**Exemple:**
1. Cliquer sur `POST /resources` (vert)
2. Cliquer sur "Try it out"
3. Remplir le JSON:
```json
{
  "name": "Salle 101",
  "type": "room",
  "description": "Salle de réunion",
  "capacity": 20,
  "location": "Building A",
  "price": 100.0
}
```
4. Cliquer sur "Execute"
5. Voir la réponse!

### 📍 Autres documentations
- **ReDoc** (plus joli): http://localhost:8002/redoc
- **OpenAPI JSON**: http://localhost:8002/openapi.json

---

## 2️⃣ TESTER AVEC CURL (Terminal)

### ✅ Health Check
```bash
curl http://localhost:8002/health
```

**Réponse attendue:**
```json
{"status":"healthy","service":"inventory-service"}
```

---

### ✅ Créer une ressource
```bash
curl -X POST "http://localhost:8002/resources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Salle 101",
    "type": "room",
    "description": "Salle de réunion",
    "capacity": 20,
    "location": "Building A",
    "price": 100.0
  }'
```

**Réponse:**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "Salle 101",
  "type": "room",
  "description": "Salle de réunion",
  "capacity": 20,
  "location": "Building A",
  "price": 100.0,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**💾 Copier l'ID pour les tests suivants!**

---

### ✅ Récupérer une ressource
```bash
# Remplacer UUID par l'ID retourné précédemment
curl "http://localhost:8002/resources/f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

---

### ✅ Lister toutes les ressources
```bash
curl "http://localhost:8002/resources"
```

---

### ✅ Lister par type
```bash
curl "http://localhost:8002/resources?type=room"
```

---

### ✅ Mettre à jour une ressource
```bash
curl -X PUT "http://localhost:8002/resources/f47ac10b-58cc-4372-a567-0e02b2c3d479" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Salle 101 - Upgraded",
    "price": 150.0
  }'
```

---

### ✅ Créer un créneau de disponibilité
```bash
# D'abord, obtenir le ID de la ressource depuis les étapes précédentes
RESOURCE_ID="f47ac10b-58cc-4372-a567-0e02b2c3d479"

curl -X POST "http://localhost:8002/resources/$RESOURCE_ID/availability" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "'$RESOURCE_ID'",
    "start_time": "2024-02-01T09:00:00",
    "end_time": "2024-02-01T17:00:00",
    "quantity": 2
  }'
```

---

### ✅ Vérifier la disponibilité
```bash
RESOURCE_ID="f47ac10b-58cc-4372-a567-0e02b2c3d479"

curl "http://localhost:8002/resources/$RESOURCE_ID/availability/check?start_time=2024-02-01T10:00:00&end_time=2024-02-01T12:00:00&quantity=1"
```

---

### ✅ Récupérer les créneaux disponibles
```bash
RESOURCE_ID="f47ac10b-58cc-4372-a567-0e02b2c3d479"

curl "http://localhost:8002/resources/$RESOURCE_ID/availability?start_time=2024-02-01T08:00:00&end_time=2024-02-01T18:00:00"
```

---

### ✅ Désactiver/Activer une ressource
```bash
RESOURCE_ID="f47ac10b-58cc-4372-a567-0e02b2c3d479"

# Désactiver
curl -X POST "http://localhost:8002/resources/$RESOURCE_ID/deactivate"

# Activer
curl -X POST "http://localhost:8002/resources/$RESOURCE_ID/activate"
```

---

## 3️⃣ TESTER AVEC PYTEST (Tests automatisés)

### ✅ Installer pytest
```bash
pip install pytest pytest-asyncio httpx
```

### ✅ Créer un fichier de test
**Créer:** `tests/test_api.py`

```python
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health():
    """Test le health check."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_resource():
    """Test la création d'une ressource."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/resources",
            json={
                "name": "Salle Test",
                "type": "room",
                "description": "Test",
                "capacity": 10,
                "location": "Test Location",
                "price": 50.0
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Salle Test"
        assert data["type"] == "room"
        assert "id" in data


@pytest.mark.asyncio
async def test_get_resource():
    """Test la récupération d'une ressource."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Créer d'abord
        create_response = await client.post(
            "/resources",
            json={
                "name": "Salle 102",
                "type": "room",
                "description": "Test",
                "capacity": 15,
                "location": "Test",
                "price": 75.0
            }
        )
        resource_id = create_response.json()["id"]
        
        # Récupérer
        get_response = await client.get(f"/resources/{resource_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == resource_id


@pytest.mark.asyncio
async def test_list_resources():
    """Test la liste des ressources."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/resources")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_resource():
    """Test la mise à jour d'une ressource."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Créer d'abord
        create_response = await client.post(
            "/resources",
            json={
                "name": "Old Name",
                "type": "room",
                "description": "Test",
                "capacity": 10,
                "location": "Test",
                "price": 50.0
            }
        )
        resource_id = create_response.json()["id"]
        
        # Mettre à jour
        update_response = await client.put(
            f"/resources/{resource_id}",
            json={"name": "New Name", "price": 100.0}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "New Name"
        assert data["price"] == 100.0


@pytest.mark.asyncio
async def test_create_availability_slot():
    """Test la création d'un créneau."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Créer une ressource d'abord
        resource_response = await client.post(
            "/resources",
            json={
                "name": "Salle Test",
                "type": "room",
                "description": "Test",
                "capacity": 10,
                "location": "Test",
                "price": 50.0
            }
        )
        resource_id = resource_response.json()["id"]
        
        # Créer un créneau
        start = datetime.now() + timedelta(days=1)
        end = start + timedelta(hours=8)
        
        slot_response = await client.post(
            f"/resources/{resource_id}/availability",
            json={
                "resource_id": resource_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "quantity": 1
            }
        )
        assert slot_response.status_code == 201
        assert "id" in slot_response.json()


@pytest.mark.asyncio
async def test_check_availability():
    """Test la vérification de disponibilité."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Créer une ressource
        resource_response = await client.post(
            "/resources",
            json={
                "name": "Salle Test",
                "type": "room",
                "description": "Test",
                "capacity": 10,
                "location": "Test",
                "price": 50.0
            }
        )
        resource_id = resource_response.json()["id"]
        
        # Créer un créneau
        start = datetime.now() + timedelta(days=1)
        end = start + timedelta(hours=8)
        
        await client.post(
            f"/resources/{resource_id}/availability",
            json={
                "resource_id": resource_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "quantity": 2
            }
        )
        
        # Vérifier la disponibilité
        check_start = (start + timedelta(hours=1)).isoformat()
        check_end = (start + timedelta(hours=3)).isoformat()
        
        check_response = await client.get(
            f"/resources/{resource_id}/availability/check",
            params={
                "start_time": check_start,
                "end_time": check_end,
                "quantity": 1
            }
        )
        assert check_response.status_code == 200
        assert check_response.json()["is_available"] == True


@pytest.mark.asyncio
async def test_deactivate_resource():
    """Test la désactivation d'une ressource."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Créer d'abord
        create_response = await client.post(
            "/resources",
            json={
                "name": "Salle Test",
                "type": "room",
                "description": "Test",
                "capacity": 10,
                "location": "Test",
                "price": 50.0
            }
        )
        resource_id = create_response.json()["id"]
        
        # Désactiver
        response = await client.post(f"/resources/{resource_id}/deactivate")
        assert response.status_code == 200
        assert response.json()["is_active"] == False
```

---

### ✅ Créer un fichier pytest.ini
**Créer:** `pytest.ini`

```ini
[pytest]
testpaths = tests
pythonpaths = .
asyncio_mode = auto
```

---

### ✅ Lancer les tests
```bash
# Tous les tests
pytest

# Avec verbose
pytest -v

# Avec coverage
pytest --cov=application --cov=domain tests/

# Un test spécifique
pytest tests/test_api.py::test_create_resource -v
```

---

## 🔧 SCRIPT DE TEST COMPLET (Copier-coller)

Créer un fichier `run_tests.py`:

```python
#!/usr/bin/env python
"""
Script de test complet du Inventory Service
"""
import subprocess
import sys

def run_tests():
    """Exécuter tous les tests."""
    print("=" * 60)
    print("🧪 TESTING INVENTORY SERVICE")
    print("=" * 60)
    
    # 1. Health check
    print("\n1️⃣ Health Check...")
    result = subprocess.run(
        ['curl', 'http://localhost:8002/health'],
        capture_output=True
    )
    print(result.stdout.decode())
    
    # 2. Run pytest
    print("\n2️⃣ Running pytest...")
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/', '-v'],
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
    
    return result.returncode

if __name__ == "__main__":
    exit(run_tests())
```

Exécuter:
```bash
python run_tests.py
```

---

## 📝 FICHIER DE TEST SIMPLE (Démarrant)

Si vous voulez un test basique, créer `tests/test_basic.py`:

```python
import pytest
from datetime import datetime, timedelta


def test_resource_model_creation():
    """Test la création d'un modèle Resource."""
    from uuid import uuid4
    from domain.models.resource import Resource, ResourceType
    
    resource = Resource(
        id=uuid4(),
        name="Salle Test",
        type=ResourceType.ROOM,
        description="Test",
        capacity=10,
        location="Test Location",
        price=50.0,
        created_at=datetime.now()
    )
    
    assert resource.name == "Salle Test"
    assert resource.capacity == 10
    assert resource.is_active == True


def test_resource_validation():
    """Test la validation d'une ressource."""
    from uuid import uuid4
    from domain.models.resource import Resource, ResourceType
    
    # Capacité invalide
    with pytest.raises(ValueError):
        Resource(
            id=uuid4(),
            name="Test",
            type=ResourceType.ROOM,
            description="Test",
            capacity=-1,  # ❌ Invalide
            location="Test",
            price=50.0,
            created_at=datetime.now()
        )


def test_availability_slot_creation():
    """Test la création d'un créneau."""
    from uuid import uuid4
    from domain.models.availability import AvailabilitySlot
    
    start = datetime.now()
    end = start + timedelta(hours=8)
    
    slot = AvailabilitySlot(
        id=uuid4(),
        resource_id=uuid4(),
        start_time=start,
        end_time=end,
        is_available=True
    )
    
    assert slot.is_available == True
    assert slot.get_duration_minutes() == 480  # 8 heures


def test_availability_slot_overlap():
    """Test la détection de chevauchement."""
    from uuid import uuid4
    from domain.models.availability import AvailabilitySlot
    
    resource_id = uuid4()
    start = datetime.now()
    
    slot1 = AvailabilitySlot(
        id=uuid4(),
        resource_id=resource_id,
        start_time=start,
        end_time=start + timedelta(hours=4),
        is_available=True
    )
    
    slot2 = AvailabilitySlot(
        id=uuid4(),
        resource_id=resource_id,
        start_time=start + timedelta(hours=2),  # Chevauche slot1
        end_time=start + timedelta(hours=6),
        is_available=True
    )
    
    assert slot1.is_overlapping_with(slot2) == True
```

Lancer:
```bash
pytest tests/test_basic.py -v
```

---

## 🎯 RÉSUMÉ DES APPROCHES

| Approche | Outil | Facilité | Automatisation |
|----------|-------|---------|----------------|
| **Web UI** | Swagger | ⭐⭐⭐⭐⭐ | ❌ |
| **Terminal** | curl | ⭐⭐⭐⭐ | ⚠️ |
| **Tests auto** | pytest | ⭐⭐⭐ | ✅ |

---

## 📊 EXEMPLE COMPLET D'UTILISATION

```bash
# 1. Démarrer le service
python main.py

# 2. Dans un autre terminal, tester
# Option A: Swagger (http://localhost:8002/docs)
# Option B: curl (voir exemples ci-dessus)
# Option C: pytest
pytest tests/ -v
```

---

## ✅ CHECKLIST DE TESTS

- [ ] ✅ Health check fonctionne
- [ ] ✅ Créer une ressource
- [ ] ✅ Récupérer une ressource
- [ ] ✅ Lister les ressources
- [ ] ✅ Mettre à jour une ressource
- [ ] ✅ Créer un créneau de disponibilité
- [ ] ✅ Vérifier la disponibilité
- [ ] ✅ Désactiver une ressource
- [ ] ✅ Tous les tests pytest passent

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ Lancer le service: `python main.py`
2. ✅ Tester avec Swagger: `http://localhost:8002/docs`
3. ✅ Ou utiliser curl pour tester
4. ✅ Écrire des tests pytest

**Bon testing!** 🎉
