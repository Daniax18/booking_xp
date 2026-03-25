# 🚀 QUICK TEST GUIDE - 3 Façons de tester

## ✅ FAÇON 1: Web Interface (La plus facile!)

### Démarrer le service
```bash
python main.py
```

### Aller à: http://localhost:8002/docs

### Cliquer sur les endpoints et cliquer "Try it out"
- Vous pouvez tester directement dans le navigateur
- Pas besoin de code!

**Exemple screenshot:** 
Les endpoints sont bien listés avec bouton "Try it out"

---

## ✅ FAÇON 2: CURL (Terminal)

### Test rapide
```bash
# Health check
curl http://localhost:8002/health

# Créer une ressource
curl -X POST "http://localhost:8002/resources" \
  -H "Content-Type: application/json" \
  -d '{"name":"Salle 101","type":"room","description":"Test","capacity":20,"location":"A","price":100}'

# Lister
curl "http://localhost:8002/resources"
```

**Voir:** TESTING.md pour les exemples complétss

---

## ✅ FAÇON 3: PYTEST (Tests automatisés)

### Installation
```bash
pip install pytest pytest-asyncio httpx
```

### Lancer tous les tests
```bash
pytest
```

### Lancer avec plus de détails
```bash
pytest -v
pytest -v --tb=short
```

### Lancer un test spécifique
```bash
pytest tests/test_resources.py::TestCreateResource::test_create_resource_success -v
```

### Avec coverage
```bash
pytest --cov=application --cov=domain tests/
```

---

## 🎯 Structure des tests (déjà créée)

```
tests/
├── __init__.py
├── conftest.py          (fixtures communes)
├── test_health.py       (health check)
├── test_resources.py    (CRUD ressources)
└── test_availability.py (disponibilité)
```

---

## 📊 Résumé des 3 façons

| Façon | Outil | Rapidité | Automatisation |
|-------|-------|----------|----------------|
| Web | Swagger | ⚡⚡⚡⚡⚡ | ❌ |
| Curl | Terminal | ⚡⚡⚡ | ⚠️ |
| Pytest | Python | ⚡ | ✅✅✅ |

---

## 🔥 Démarrage immédiat

```bash
# Terminal 1: Lancer le service
python main.py

# Terminal 2: Lancer les tests
pytest tests/ -v
```

---

**Voir TESTING.md pour la documentation complète!** 📖
