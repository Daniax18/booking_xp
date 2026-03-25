# 🚀 QUICK START GUIDE - Inventory Service

## Installation rapide (5 minutes)

### 1. Prérequis
```bash
# Vérifier que Python 3.9+ est installé
python --version
```

### 2. Setup
```bash
# Naviguer dans le répertoire
cd api/inventory-service

# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Copier la configuration
copy .env.example .env
```

### 3. Lancer le service
```bash
python main.py
```

✅ Service disponible à: **http://localhost:8002**

---

## Test rapide avec curl

### 1️⃣ Créer une ressource
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

### 2️⃣ Récupérer la ressource
```bash
# Remplacer UUID par l'ID retourné précédemment
curl "http://localhost:8002/resources/{UUID}"
```

### 3️⃣ Lister les ressources
```bash
curl "http://localhost:8002/resources"
```

### 4️⃣ Créer une disponibilité
```bash
curl -X POST "http://localhost:8002/resources/{UUID}/availability" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "{UUID}",
    "start_time": "2024-01-20T09:00:00",
    "end_time": "2024-01-20T17:00:00",
    "quantity": 2
  }'
```

### 5️⃣ Vérifier la disponibilité
```bash
curl "http://localhost:8002/resources/{UUID}/availability/check?start_time=2024-01-20T10:00:00&end_time=2024-01-20T12:00:00&quantity=1"
```

---

## Documentation interactive

Accédez à la documentation interactive à:
- **Swagger**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

---

## Structure du code expliquée

```
domain/             ← Logique métier pure (indépendante)
application/        ← Orchestration de la logique (use cases)
infrastructure/     ← Détails techniques (BD, HTTP, etc.)
```

---

## Fichiers importants

- `main.py` - Point d'entrée FastAPI
- `config.py` - Configuration centralisée
- `logger.py` - Logging personnalisé
- `application/dtos.py` - Validation des requêtes/réponses
- `domain/exceptions.py` - Exceptions métier
- `README.md` - Documentation complète
- `IMPROVEMENTS.md` - Résumé des améliorations

---

## Variables d'environnement

```env
DATABASE_URL=sqlite:///./inventory_service.db  # ou PostgreSQL, MySQL
LOG_LEVEL=INFO                                   # DEBUG, INFO, WARNING, ERROR
HOST=0.0.0.0                                     # Adresse d'écoute
PORT=8002                                        # Port
DEBUG=False                                      # Mode debug
ENVIRONMENT=development                          # development ou production
```

---

## Commandes utiles

```bash
# Format/Lint le code
black . && flake8 .

# Lancer les tests
pytest tests/

# Générer les migrations (pour la future BD)
alembic init alembic

# Lancer en mode production
gunicorn -w 4 -b 0.0.0.0:8002 main:app
```

---

## Support

Pour plus de détails:
- Voir `README.md` pour la documentation complète
- Voir `IMPROVEMENTS.md` pour les améliorations détaillées
- Voir les docstrings dans le code (avec type hints complets)

**Bonne chance avec votre projet! 🎉**
